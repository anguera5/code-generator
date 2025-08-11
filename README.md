# Code Generation App

A minimal code generation app with FastAPI backend and Vue 3 (Vite + Vuetify + Monaco) frontend.

## Prereqs
- Docker and Docker Compose
- OpenAI API key

## Quick start (Docker Compose)
1. Copy backend/.env.example to backend/.env and set OPENAI_API_KEY.
2. Run: `docker compose up --build`
3. Open http://localhost:5173

## Backend
- FastAPI, endpoints:
  - POST /api/generate { prompt, language }
  - POST /api/tests { code, language }
  - POST /api/docs { code, language }
- Env vars: OPENAI_API_KEY, OPENAI_MODEL (default gpt-3.5-turbo)

## Frontend
- Vue 3 + Vite + TypeScript + Vuetify + Monaco
- Features: prompt input, language select (python/java), Generate, Add Unit Tests, Add Documentation, copy/download

## Notes
- Stateless API, no DB.
- For dev outside Docker, install deps in frontend and backend respectively.
