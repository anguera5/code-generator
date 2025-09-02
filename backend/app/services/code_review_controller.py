from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import HTTPException

from app.services.github_app import GitHubApp
from app.services.llm_model import LLMModel


class CodeReviewController:
    """Coordinates webhook verification, parsing, LLM review, and posting as GitHub App bot."""

    def __init__(self, llm: LLMModel, gh_app: GitHubApp) -> None:
        self.llm = llm
        self.gh_app = gh_app

    def parse_payload(self, raw_body: bytes, form_or_query_payload: str | None) -> Dict[str, Any]:
        # Prefer explicit 'payload' field if present (form/query)
        if form_or_query_payload:
            try:
                return json.loads(str(form_or_query_payload))
            except Exception as e:  # noqa: BLE001
                raise HTTPException(status_code=422, detail=f"Invalid JSON in 'payload' field: {e}") from e
        # Else parse the raw body as JSON
        try:
            data = json.loads(raw_body.decode("utf-8") or "{}")
            if not isinstance(data, dict):
                raise ValueError("Payload must be a JSON object")
            return data
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=422, detail="Input should be a valid JSON object or a form field 'payload' with JSON") from e

    def verify_signature_or_raise(self, headers: Dict[str, str], body: bytes) -> None:
        if not self.gh_app.verify_signature(headers, body):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    def signature_valid(self, headers: Dict[str, str], body: bytes) -> bool:
        """Non-raising check for webhook signature validity."""
        return self.gh_app.verify_signature(headers, body)

    def extract_pr_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pr = payload.get("pull_request") or {}
        repo_obj = payload.get("repository") or {}
        owner_obj = (repo_obj.get("owner") or {})
        context = {
            "action": payload.get("action"),
            "title": pr.get("title") or "(untitled PR)",
            "body": pr.get("body") or "",
            "base_branch": (pr.get("base") or {}).get("ref"),
            "head_branch": (pr.get("head") or {}).get("ref"),
            "diff_url": pr.get("diff_url"),
            "repository_full": repo_obj.get("full_name"),
            "owner": owner_obj.get("login"),
            "repo": repo_obj.get("name"),
            "pr_number": payload.get("number") or pr.get("number"),
            "installation_id": (payload.get("installation") or {}).get("id"),
        }
        return context

    def diff_summary(self, ctx: Dict[str, Any]) -> str:
        repo = ctx.get("repository_full")
        base_b = ctx.get("base_branch")
        head_b = ctx.get("head_branch")
        diff_url = ctx.get("diff_url")
        if repo or base_b or head_b or diff_url:
            return f"Repository: {repo}\nBase: {base_b} -> Head: {head_b}\nDiff URL: {diff_url}"
        return "(no diff metadata provided)"

    def generate_review_text(self, title: str, body: str, diff_summary: str) -> str:
        # Ensure LLM client is initialized for server-initiated webhook (no explicit api_key param)
        if getattr(self.llm, "llm", None) is None:
            import os
            env_key = os.getenv("OPENAI_API_KEY", "").strip()
            if env_key:
                # May raise HTTPException if invalid; caller handles
                self.llm.check_model_running(env_key)
        return self.llm.generate_code_review(title, body, diff_summary)

    def try_post_review(self, ctx: Dict[str, Any], review_text: str) -> None:
        installation_id = ctx.get("installation_id")
        owner = ctx.get("owner")
        repo = ctx.get("repo")
        pr_number = ctx.get("pr_number")
        if installation_id and owner and repo and pr_number:
            # Build minimal inline comments if possible
            comments = self._build_inline_comments(ctx, review_text)
            print(f"[CODE-REVIEW] Inline comments prepared: {len(comments)}")
            if comments:
                preview = [{"path": c.get("path"), "position": c.get("position")} for c in comments[:3]]
                print(f"[CODE-REVIEW] Inline preview (first 3): {preview}")
            try:
                self.gh_app.post_pull_request_review(
                    installation_id=int(installation_id),
                    owner=str(owner),
                    repo=str(repo),
                    pr_number=int(pr_number),
                    body=review_text,
                    comments=comments if comments else None,
                )
                print("[CODE-REVIEW] Review posted (with inline comments).")
            except RuntimeError as e:
                # If inline positions are invalid (422), retry with summary-only review
                if "422" in str(e):
                    print("[CODE-REVIEW] Inline comments rejected by GitHub (422). Retrying without inline comments.")
                    self.gh_app.post_pull_request_review(
                        installation_id=int(installation_id),
                        owner=str(owner),
                        repo=str(repo),
                        pr_number=int(pr_number),
                        body=review_text,
                        comments=None,
                    )
                    print("[CODE-REVIEW] Review posted (summary-only).")
                else:
                    raise

    # -------- Inline comments --------
    def _build_inline_comments(self, ctx: Dict[str, Any], review_text: str) -> list[dict]:
        """Use the LLM to generate targeted inline comments on added lines only.

        We number the unified diff lines to match GitHub's expected 'position' and provide the set
        of allowed positions (only '+' lines). The LLM must choose positions from that set.
        """
        installation_id = ctx.get("installation_id")
        owner = ctx.get("owner")
        repo = ctx.get("repo")
        pr_number = ctx.get("pr_number")
        if not (installation_id and owner and repo and pr_number):
            return []

        try:
            files = self.gh_app.get_pull_files(
                int(installation_id), str(owner), str(repo), int(pr_number)
            )
        except (RuntimeError, ValueError, TypeError):
            # If the file list cannot be fetched, fall back to summary-only review
            return []
        print(f"[CODE-REVIEW] PR files fetched: {len(files)}")

        # Ensure LLM is initialized (reuse OPENAI_API_KEY if needed)
        if getattr(self.llm, "llm", None) is None:
            import os
            env_key = os.getenv("OPENAI_API_KEY", "").strip()
            if env_key:
                self.llm.check_model_running(env_key)

        inline: list[dict] = []
        max_total = 10
        max_per_file = 3
        first_fallback: dict | None = None
        for f in files:
            if len(inline) >= max_total:
                break
            path = f.get("filename")
            patch: str | None = f.get("patch")
            if not path or not patch:
                continue
            # Compute allowed positions (only added lines), and build numbered patch
            lines = patch.splitlines()
            allowed_positions: list[int] = []
            numbered = []
            for i, line in enumerate(lines, start=1):
                if line.startswith("+") and not line.startswith("+++"):
                    allowed_positions.append(i)
                numbered.append(f"{i:05d}: {line}")

            if not allowed_positions:
                continue
            if first_fallback is None:
                first_fallback = {
                    "path": path,
                    "position": allowed_positions[0],
                    "body": "Automated review: please double-check this change (see summary).",
                }

            # Ask the LLM to produce at most max_per_file inline comments in strict JSON
            prompt = (
                "You are a senior code reviewer. Given a single-file unified diff, suggest at most "
                f"{max_per_file} high-signal inline comments ONLY on added lines.\n"
                "Focus on issues like secrets/tokens, unsafe patterns (eval/exec, subprocess shell=True, "
                "os.system, pickle.loads), TLS verify=False, and clear bad practices.\n"
                "Use the provided AllowedPositions (unified diff indexes) and choose positions strictly from it.\n"
                "Return STRICT JSON with this shape: {\"comments\": [{\"position\": <int>, \"body\": \"<short suggestion>\"}, ...]}\n"
                "Do not include code fences or any text outside JSON. Keep bodies concise (<= 200 chars).\n"
                "Contextual Summary (may inform prioritization, do not reference it in comments):\n"
                + (review_text[:300] if isinstance(review_text, str) else "")
                + "\n"
                f"Path: {path}\n"
                f"AllowedPositions: {allowed_positions}\n"
                "UnifiedDiffWithPositions:\n"
                + "\n".join(numbered)
            )

            try:
                resp = self.llm.llm.invoke(prompt)
                text = getattr(resp, "content", str(resp)) or "{}"
                print(f"[CODE-REVIEW] LLM inline raw (trunc): {text[:200].replace('\n', ' ')}...")
                obj = self._safe_parse_json(text)
                comments = obj.get("comments") if isinstance(obj, dict) else None
                if not isinstance(comments, list):
                    print("[CODE-REVIEW] LLM inline: no comments array found.")
                    continue
                per_file: list[dict] = []
                for c in comments:
                    if not isinstance(c, dict):
                        continue
                    pos = c.get("position")
                    body = c.get("body")
                    if isinstance(pos, int) and pos in allowed_positions and isinstance(body, str) and body.strip():
                        per_file.append({"path": path, "position": pos, "body": body.strip()})
                    if len(per_file) >= max_per_file:
                        break
                print(f"[CODE-REVIEW] LLM inline accepted for {path}: {len(per_file)} (allowed: {len(allowed_positions)})")
                inline.extend(per_file)
            except (ValueError, TypeError):
                print("[CODE-REVIEW] LLM inline: parsing error; skipping file.")
                continue

            if len(inline) >= max_total:
                break
        if not inline and first_fallback is not None:
            print("[CODE-REVIEW] Inline empty after LLM; adding single fallback inline comment.")
            inline.append(first_fallback)
        return inline

        
    def _first_added_position(self, patch: str) -> int | None:
        """Return the first position index suitable for PR review comment.

        GitHub's Pull Request Reviews API expects 'position' to be the index in the unified diff.
        We count lines from the start of the patch hunk text, including context and headers.
        """
        pos = 0
        found_any = False
        for line in patch.splitlines():
            pos += 1
            # Skip file headers ---/+++ or hunk headers @@ ... @@ by counting them as positions
            if line.startswith("@@"):
                # Reset per-hunk position? For unified diff positions, we continue counting overall
                # to match GitHub's expectation for the 'files' diff.
                continue
            if line.startswith("+") and not line.startswith("+++"):
                found_any = True
                break
        return pos if found_any else None

    def _safe_parse_json(self, text: str) -> dict:
        """Parse JSON output from the model, tolerating optional code fences.

        Returns an empty dict on failure.
        """
        s = text.strip()
        # Strip markdown fences if present
        if s.startswith("```") and s.endswith("```"):
            s = s.strip("`")
            # Remove possible language hint
            first_nl = s.find("\n")
            if first_nl != -1:
                s = s[first_nl + 1 :]
        try:
            return json.loads(s)
        except (json.JSONDecodeError, ValueError):  # return empty on invalid JSON
            return {}
