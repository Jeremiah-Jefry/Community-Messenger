# Community Messenger

Real-time chat app. The backend is FastAPI + SQLAlchemy, the frontend is React 19 + Vite.
WebSockets are not implemented yet; the API currently covers registration, login,
the current-user endpoint and rooms with message history.

## Layout

```
backend/    FastAPI app (auth + rooms, SQLite by default)
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
alembic upgrade head            # create or update the database schema
uvicorn main:app --reload
```

Interactive docs are at http://127.0.0.1:8000/docs. Use **Authorize** there with the
username and password you registered.

### Migrations

The schema is owned by Alembic; `main.py` never creates tables itself. The database URL
comes from `SQLALCHEMY_DATABASE_URL`, so migrations always target the configured database.

```bash
alembic revision --autogenerate -m "describe the change"   # after editing models.py
alembic upgrade head                                         # apply
alembic downgrade -1                                         # roll back one step
alembic current                                              # applied revision
```

### Backend checks

```bash
ruff check .
pytest -q
```

Tests run against a separate in-memory SQLite database created by the Alembic
migrations, and never touch `messenger.db`.

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
| POST   | `/rooms`  | yes  | Create a room, caller becomes `owner` (201) |
| GET    | `/rooms`  | yes  | Rooms the caller belongs to              |
| POST   | `/rooms/{id}/join` | yes | Join a room as `member` (idempotent) |
| GET    | `/rooms/{id}/messages` | yes | Newest-first message page, members only |
| WS     | `/ws`    | yes  | Room realtime socket, see below          |

`GET /rooms/{id}/messages` takes `before=<message_id>` (exclusive cursor, defaults to none)
and `limit` (1-100, default 50). Non-members get `403`.

Tokens are HS256 JWTs signed with `SECRET_KEY` and expire after
`ACCESS_TOKEN_EXPIRE_MINUTES`. Passwords are hashed with bcrypt using a per-user salt.

## WebSocket API

`POST /login` returns `access_token` plus a short-lived `ws_token` (an HS256 JWT with
`type: "ws"`, valid for `WS_TOKEN_EXPIRE_MINUTES`). Browsers cannot set headers on a
WebSocket handshake, so the ticket travels in the query string:

```
ws://<host>/ws?room_id=<room id>&token=<ws_token>
```

The socket is accepted, then closed immediately with `4401` if the ticket is missing,
expired, tampered with, or is a bearer `access_token`, and with `4403` if the user is not
a member of the room. Sockets are held per room in memory; sending on multiple uvicorn
workers needs the Redis fan-out from a later phase.

Every frame is a JSON object with a `type` field.

### Client to server

| Type          | Fields                | Behaviour                                        |
| ------------- | --------------------- | ------------------------------------------------ |
| `message.send`| `content` (1-2000)    | Persists the message, then broadcasts `message.new` |
| `typing`      | `is_typing` (bool)    | Broadcasts `typing`, not persisted               |

### Server to client

| Type         | Fields                                    |
| ------------ | ----------------------------------------- |
| `message.new`| `message` (`MessageOut`)                  |
| `typing`     | `user_id`, `username`, `is_typing`        |
| `error`      | `code`, `detail`                          |

`error.code` is one of `invalid_json`, `invalid_event`, `unsupported_frame`,
`internal_error`. Malformed events are reported to the sender and never disconnect the
socket; an unexpected server-side failure closes it with `1011`.

```json
// client
{"type": "message.send", "content": "hello"}
// server, to every socket in the room including the sender
{"type": "message.new", "message": {"id": 1, "room_id": 1, "sender_id": 1, "content": "hello", "created_at": "2026-01-01T00:00:00", "edited_at": null, "deleted_at": null}}
```
