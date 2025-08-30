# Backend - FastAPI

Run locally:
- Python 3.11
- Create virtualenv, then `pip install -e .`
- `uvicorn app.main:app --reload`

Env:
- OPENAI_API_KEY
- OPENAI_BASE_URL (optional)
- OPENAI_MODEL (default gpt-3.5-turbo)

## Timeouts
- LLM calls use a request timeout of ~55s to avoid long hangs.
- The ChemBL pipeline has a soft overall timeout of 55s and will return an HTTP 400 with a friendly message if exceeded.
