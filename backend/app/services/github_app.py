import os
import hmac
import hashlib
from typing import Optional, Dict, Any

import httpx

API_ROOT = "https://api.github.com"
API_VER = "2022-11-28"


class GitHubApp:
    """Minimal GitHub client using a personal token; includes webhook signature verification."""

    def __init__(self, webhook_secret: Optional[str] = None) -> None:
        self.webhook_secret = webhook_secret or os.getenv("GITHUB_WEBHOOK_SECRET")
        self.personal_token = (
            os.getenv("GITHUB_PERSONAL_TOKEN")
            or os.getenv("GITHUB_TOKEN")
            or os.getenv("GH_TOKEN")
        )
        if not self.personal_token:
            print("[GitHub] Warning: No personal token set (GITHUB_PERSONAL_TOKEN/GITHUB_TOKEN/GH_TOKEN)")

    # --------- Webhook Security ---------
    def verify_signature(self, headers: Dict[str, str], body: bytes) -> bool:
        if not self.webhook_secret:
            return True  # not enforced
        # Normalize header keys (case-insensitive)
        hdrs = {str(k).lower(): v for k, v in headers.items()}
        sha256_sig = hdrs.get("x-hub-signature-256")
        sha1_sig = hdrs.get("x-hub-signature")

        # Prefer sha256; fall back to sha1 if present
        if sha256_sig and sha256_sig.startswith("sha256="):
            digest = hmac.new(self.webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            expected = f"sha256={digest}"
            return hmac.compare_digest(expected, sha256_sig)
        if sha1_sig and sha1_sig.startswith("sha1="):
            digest = hmac.new(self.webhook_secret.encode("utf-8"), body, hashlib.sha1).hexdigest()
            expected = f"sha1={digest}"
            return hmac.compare_digest(expected, sha1_sig)
        return False

    # --------- PR Reviews ---------
    def post_pull_request_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        comments: Optional[list[dict]] = None,
        event: str = "COMMENT",
    ) -> Dict[str, Any]:
        url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VER,
            "Authorization": f"token {self.personal_token}",
        }
        payload: Dict[str, Any] = {"body": body, "event": event}
        if comments:
            payload["comments"] = comments

        with httpx.Client(timeout=20) as client:
            resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 300:
            raise RuntimeError(f"Posting PR review failed: {resp.status_code} {resp.text}")
        return resp.json()

    def get_pull_files(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        per_page: int = 100,
    ) -> list[Dict[str, Any]]:
        """Fetch the list of changed files for a PR, including unified patches.

        Note: For large PRs this may be paginated; we fetch up to `per_page` (default 100).
        """
        url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr_number}/files?per_page={per_page}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VER,
            "Authorization": f"token {self.personal_token}",
        }
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers=headers)
        if resp.status_code >= 300:
            raise RuntimeError(f"Fetching PR files failed: {resp.status_code} {resp.text}")
        return resp.json()
