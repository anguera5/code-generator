# Backend - FastAPI

FastAPI service powering code generation, website RAG, and the ChEMBL SQL RAG pipeline.

## Run locally
- Python 3.11+
- Create virtualenv, then `pip install -e .`
- `uvicorn app.main:app --reload`

## Environment
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` (optional)
- `OPENAI_MODEL` (default from settings)
- `OPENAI_EMBEDDING_MODEL` (default from settings)
- `CHEMBL_SQLITE_PATH` (default `app/chembl/chembl_35.db`)
- `CHEMBL_PIPELINE_TIMEOUT_S` (soft budget for full pipeline; 0 disables)

## ChEMBL SQL RAG
- LangGraph pipeline: classify → plan → retrieve → process → synthesize → execute → repair (loop‑capped)
- Edit entrypoint for minimal SQL changes
- Safe execution: SELECT/WITH only, forbid DDL/DML, enforce LIMIT
- Session memory (`memory_id`) supports edits and LIMIT re‑execute

## Timeouts
- Upstream LLM calls have per-call timeouts.
- Pipeline soft timeout is configurable via `CHEMBL_PIPELINE_TIMEOUT_S`. Default 0 (disabled) so long DB queries aren’t killed. Set a value if you need a hard cap.
