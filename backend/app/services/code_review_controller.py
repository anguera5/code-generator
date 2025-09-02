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
            try:
                self.gh_app.post_pull_request_review(
                    installation_id=int(installation_id),
                    owner=str(owner),
                    repo=str(repo),
                    pr_number=int(pr_number),
                    body=review_text,
                    comments=comments if comments else None,
                )
            except RuntimeError as e:
                # If inline positions are invalid (422), retry with summary-only review
                if "422" in str(e):
                    self.gh_app.post_pull_request_review(
                        installation_id=int(installation_id),
                        owner=str(owner),
                        repo=str(repo),
                        pr_number=int(pr_number),
                        body=review_text,
                        comments=None,
                    )
                else:
                    raise

    # -------- Inline comments --------
    def _build_inline_comments(self, ctx: Dict[str, Any], review_text: str) -> list[dict]:
        """Create a few safe inline comments to anchor the review.

        This minimal strategy avoids complex diff mapping by attaching a single comment to the
        first hunk of up to 3 changed files, placing it at the first added/modified line.
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

        inline: list[dict] = []
        # Very simple patch parser to find first added line position in the diff for each file
        for f in files[:3]:  # limit comments to first 3 files to avoid noise
            path = f.get("filename")
            patch: str | None = f.get("patch")
            if not path or not patch:
                continue
            position = self._first_added_position(patch)
            if position is None:
                continue
            # Use a brief hint drawn from the overall review to make the inline actionable
            snippet = (review_text or "").splitlines()[0:1]
            hint = snippet[0] if snippet else "Consider improvements here."
            inline.append({
                "path": path,
                "position": position,
                "body": f"Suggestion: {hint}",
            })
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
