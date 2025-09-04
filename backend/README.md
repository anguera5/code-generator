# Backend - FastAPI

FastAPI service powering code generation, website RAG, and the ChEMBL Agent pipeline.

## Run locally
- Python 3.11+
- Create virtualenv, then `pip install -e .`
- `uvicorn app.main:app --reload`

## Code Review (GitHub)

- Webhook endpoint: `POST /api/code-review/webhook`
	- Events: select Pull requests ONLY.
	- Secret: supported via `GITHUB_WEBHOOK_SECRET` but may be left empty.
	- Scope: public repositories.
- Direct trigger endpoint: `POST /api/code-review/by-url { url }` to kick off a review for an existing PR.
- Reviews are posted as the maintainer account: `@anguera5` (handled server-side; no client secrets).

Notes:
- Session memory (`memory_id`) supports edits and LIMIT re‑execute (for ChEMBL module; unrelated to code review).
 
### Environment
- `GITHUB_WEBHOOK_SECRET` — optional; if set, webhook signatures are verified.

## Timeouts
- Upstream LLM calls have per-call timeouts.
- Pipeline soft timeout is configurable via `CHEMBL_PIPELINE_TIMEOUT_S`. Default 0 (disabled) so long DB queries aren’t killed. Set a value if you need a hard cap.
