# Backend - FastAPI

FastAPI service powering code generation, website RAG, and the ChEMBL SQL RAG pipeline.

## Run locally
- Python 3.11+
- Create virtualenv, then `pip install -e .`
- `uvicorn app.main:app --reload`

## Environment

### GitHub App (code review bot)
- `GITHUB_APP_ID` (integer App ID)
- `GITHUB_WEBHOOK_SECRET` (string used to verify `X-Hub-Signature-256`)
- One of the following for the private key:
	- `GITHUB_APP_PRIVATE_KEY_PATH` (filesystem path to the `.pem`), or
	- `GITHUB_APP_PRIVATE_KEY` (PEM content; supports base64 or raw with `\n`-escaped newlines)

Notes:
- The service creates a short-lived JWT (<= 10 minutes) and exchanges it for an installation token (1 hour).
- PR reviews are posted via the GitHub App installation so they appear as `<your-app-name>[bot]`.
- Do not commit your `.pem` or secrets. Use environment variables or a secret manager.

- Session memory (`memory_id`) supports edits and LIMIT re‑execute

## Timeouts
- Upstream LLM calls have per-call timeouts.
- Pipeline soft timeout is configurable via `CHEMBL_PIPELINE_TIMEOUT_S`. Default 0 (disabled) so long DB queries aren’t killed. Set a value if you need a hard cap.
