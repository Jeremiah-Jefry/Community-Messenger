from pydantic import BaseModel, Field, field_validator

from auth_utils import BCRYPT_MAX_PASSWORD_BYTES

USERNAME_PATTERN = r"^[a-zA-Z0-9_]+$"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=USERNAME_PATTERN)
    # bcrypt hashes at most the first 72 bytes of a password.
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_within_bcrypt_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError(
                f"password must not exceed {BCRYPT_MAX_PASSWORD_BYTES} bytes"
            )
        return value


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True