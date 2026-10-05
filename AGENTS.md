# Community Messenger: agent rules

## Project
Real-time chat app. Backend: FastAPI + SQLAlchemy (in /backend). Frontend: React 19 + Vite (in /frontend).
Current state: only register/login/me exist. No messaging, no WebSockets yet.

## Target architecture
- PostgreSQL (SQLite only for quick local dev), Alembic migrations
- Native FastAPI WebSockets at /ws, one ConnectionManager mapping room_id -> sockets
- Redis pub/sub for multi-instance fan-out (later phase)
- JWT auth with PyJWT only (remove python-jose), bcrypt/argon2 directly (remove passlib)
- All config via environment variables; never hardcode secrets or URLs

## Working rules
1. Read the relevant files before editing. Never assume contents.
2. Work on ONE phase at a time. Do not start the next phase.
3. Make small, reviewable changes. One logical change per commit-sized step.
4. Never invent libraries or APIs. If unsure a function exists, check the installed package or its docs.
5. After every step, run the checks (below). If a check fails, fix it before continuing. Do not skip or weaken tests to make them pass.
6. Do not delete or rewrite working code unless the task says so.
7. Do not commit, push, or modify git history. Leave changes uncommitted for my review.
8. Never create or print real secrets. Use .env.example with placeholders.
9. If a requirement is ambiguous, pick the simplest option, state the assumption in your report, and continue.

## Checks (run what exists)
- Backend: `cd backend && ruff check . && pytest -q`
- Frontend: `cd frontend && npm run lint && npm run build`
- Backend boots: `uvicorn main:app` starts without errors

## End-of-phase report (required)
List: files changed, what was done, check results (pasted output), assumptions made, anything left undone.
Then STOP and wait for my approval.