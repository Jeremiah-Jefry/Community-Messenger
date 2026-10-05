import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

BCRYPT_MAX_PASSWORD_BYTES = 72


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


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)