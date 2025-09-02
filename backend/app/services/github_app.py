import base64
import os
import time
import hmac
import hashlib
from typing import Optional, Dict, Any

import httpx

try:
    import jwt  # PyJWT
except ImportError as _e:  # pragma: no cover
    raise RuntimeError("PyJWT is required. Add 'PyJWT' to dependencies.") from _e


API_ROOT = "https://api.github.com"
API_VER = "2022-11-28"


def _load_private_key_from_env() -> Optional[str]:
    """Load the GitHub App private key from env.

    Supports either a file path (GITHUB_APP_PRIVATE_KEY_PATH) or raw/base64 content (GITHUB_APP_PRIVATE_KEY).
    """
    key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
    if key_path and os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as f:
            return f.read()

    raw = os.getenv("GITHUB_APP_PRIVATE_KEY")
    if not raw:
        return None
    # Handle escaped newlines
    if "BEGIN" in raw:
        return raw.replace("\\n", "\n")
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
        return decoded
    except (ValueError, UnicodeDecodeError):
        return raw.replace("\\n", "\n")


class GitHubApp:
    """Small helper for GitHub App auth, webhook verification, and PR review posting."""

    def __init__(
        self,
        app_id: Optional[int] = None,
        private_key_pem: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ) -> None:
        self.app_id = app_id or (int(os.getenv("GITHUB_APP_ID")) if os.getenv("GITHUB_APP_ID") else None)
        self.private_key_pem = private_key_pem or _load_private_key_from_env()
        self.webhook_secret = webhook_secret or os.getenv("GITHUB_WEBHOOK_SECRET")

        # Cache install tokens per installation id {id: {token, exp_ts}}
        self._install_token_cache: Dict[int, Dict[str, Any]] = {}

        if self.app_id is None:
            print("[GitHubApp] Warning: GITHUB_APP_ID not set; GitHub App auth disabled.")
        if not self.private_key_pem:
            print("[GitHubApp] Warning: Private key not configured; GitHub App auth disabled.")
        if not self.webhook_secret:
            print("[GitHubApp] Warning: GITHUB_WEBHOOK_SECRET not set; webhook signature verification disabled.")

    @classmethod
    def from_env(cls) -> "GitHubApp":
        return cls()

    # --------- Auth ---------
    def create_jwt(self) -> str:
        if not (self.app_id and self.private_key_pem):
            raise RuntimeError("GitHub App credentials missing (GITHUB_APP_ID/private key).")
        now = int(time.time())
        payload = {
            "iat": now - 60,  # allow small clock skew
            "exp": now + 9 * 60,  # < 10 minutes
            "iss": self.app_id,
        }
        token = jwt.encode(payload, self.private_key_pem, algorithm="RS256")
        return token.decode("utf-8") if isinstance(token, bytes) else token

    def get_installation_token(self, installation_id: int) -> str:
        now = time.time()
        cached = self._install_token_cache.get(installation_id)
        if cached and (cached.get("exp", 0) - 60) > now:
            return cached["token"]

        jwt_token = self.create_jwt()
        url = f"{API_ROOT}/app/installations/{installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VER,
        }
        with httpx.Client(timeout=20) as client:
            resp = client.post(url, headers=headers)
        if resp.status_code >= 300:
            raise RuntimeError(f"GitHub token exchange failed: {resp.status_code} {resp.text}")
        data = resp.json()
        token = data["token"]
        # Cache for ~55 minutes to be safe (official expiry is 1 hour)
        self._install_token_cache[installation_id] = {"token": token, "exp": now + 55 * 60}
        return token

    # --------- Webhook Security ---------
    def verify_signature(self, headers: Dict[str, str], body: bytes) -> bool:
        if not self.webhook_secret:
            return True  # not enforced
        sig = headers.get("X-Hub-Signature-256") or headers.get("x-hub-signature-256")
        if not sig or not sig.startswith("sha256="):
            return False
        digest = hmac.new(self.webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        expected = f"sha256={digest}"
        return hmac.compare_digest(expected, sig)

    # --------- PR Reviews ---------
    def post_pull_request_review(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        comments: Optional[list[dict]] = None,
        event: str = "COMMENT",
    ) -> Dict[str, Any]:
        token = self.get_installation_token(installation_id)
        url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VER,
        }
        payload: Dict[str, Any] = {"body": body, "event": event}
        if comments:
            payload["comments"] = comments

        with httpx.Client(timeout=20) as client:
            resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 300:
            raise RuntimeError(f"Posting PR review failed: {resp.status_code} {resp.text}")
        return resp.json()
