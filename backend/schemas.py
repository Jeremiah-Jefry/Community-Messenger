from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter, field_validator

from auth_utils import BCRYPT_MAX_PASSWORD_BYTES

USERNAME_PATTERN = r"^[a-zA-Z0-9_]+$"
MAX_MESSAGE_LENGTH = 2000


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


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank")
        return stripped


class RoomOut(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class RoomMemberOut(BaseModel):
    user_id: int
    room_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    room_id: int
    sender_id: int
    content: str = Field(max_length=MAX_MESSAGE_LENGTH)
    created_at: datetime
    edited_at: datetime | None = None
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


# --- websocket events -------------------------------------------------------


class MessageSendEvent(BaseModel):
    type: Literal["message.send"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)


class TypingEvent(BaseModel):
    type: Literal["typing"]
    is_typing: bool = True


CLIENT_EVENT = Annotated[
    Union[MessageSendEvent, TypingEvent], Field(discriminator="type")
]
CLIENT_EVENT_ADAPTER = TypeAdapter(CLIENT_EVENT)


class MessageNewEvent(BaseModel):
    type: Literal["message.new"] = "message.new"
    message: MessageOut


class TypingBroadcastEvent(BaseModel):
    type: Literal["typing"] = "typing"
    user_id: int
    username: str
    is_typing: bool


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    code: str
    detail: str