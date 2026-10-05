import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

from config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    WS_TOKEN_EXPIRE_MINUTES,
)

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Copy .env.example to .env and set SECRET_KEY "
        'to a random value, e.g. python -c "import secrets; print(secrets.token_urlsafe(32))".'
    )

BCRYPT_MAX_PASSWORD_BYTES = 72
WS_TOKEN_TYPE = "ws"


def hash_password(password: str) -> str:
    # gensalt() generates a fresh salt per call, so every user gets a unique hash.
    # bcrypt only uses the first 72 bytes of the input; schemas.UserCreate rejects
    # passwords longer than that before they reach this function.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        # Malformed hash, or an input bcrypt refuses to process.
        return False


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    minutes = ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else expires_minutes
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_ws_token(username: str) -> str:
    return create_access_token(
        {"sub": username, "type": WS_TOKEN_TYPE},
        expires_minutes=WS_TOKEN_EXPIRE_MINUTES,
    )


def decode_ws_token(token: str | None) -> str | None:
    """Return the username of a valid websocket token, otherwise None."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    if payload.get("type") != WS_TOKEN_TYPE:
        return None
    username = payload.get("sub")
    return username if isinstance(username, str) else None