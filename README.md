# Community Messenger

Real-time chat app. The backend is FastAPI + SQLAlchemy, the frontend is React 19 + Vite.
Messaging and WebSockets are not implemented yet; the API currently covers
registration, login and the current-user endpoint.

## Layout

```
backend/    FastAPI app (auth endpoints, SQLite by default)
frontend/   Vite + React client
```

## Requirements

- Python 3.11+
- Node.js 20+

## Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```

Edit `.env` and set `SECRET_KEY` to a random value. Generate one with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Startup fails with a `RuntimeError` if `SECRET_KEY` is missing. The other settings
have local defaults: `sqlite:///./messenger.db`, `http://localhost:5173` for CORS and a
60 minute access-token lifetime. Point `SQLALCHEMY_DATABASE_URL` at PostgreSQL in
deployed environments.

Run the API:

```bash
uvicorn main:app --reload
```

Interactive docs are at http://127.0.0.1:8000/docs. Use **Authorize** there with the
username and password you registered.

### Backend checks

```bash
ruff check .
pytest -q
```

Tests run against a separate in-memory SQLite database and never touch `messenger.db`.

## Frontend

```bash
cd frontend
npm ci
copy .env.example .env         # macOS/Linux: cp .env.example .env
npm run dev
```

`VITE_API_URL` in `.env` points the client at the API; it defaults to
`http://127.0.0.1:8000` in `.env.example`. Vite only exposes variables prefixed with
`VITE_`.

### Frontend checks

```bash
npm run lint
npm run build
```

## API

| Method | Path      | Auth | Description                              |
| ------ | --------- | ---- | ---------------------------------------- |
| GET    | `/`       | no   | Health check                             |
| POST   | `/register` | no | Create a user (username 3-30 `[A-Za-z0-9_]`, password 8-72) |
| POST   | `/login`  | no   | Form login, returns a bearer token       |
| GET    | `/me`     | yes  | Current user for the bearer token        |

Tokens are HS256 JWTs signed with `SECRET_KEY` and expire after
`ACCESS_TOKEN_EXPIRE_MINUTES`. Passwords are hashed with bcrypt using a per-user salt.