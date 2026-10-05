import json
import logging

from fastapi import APIRouter, Depends, Query, WebSocket
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

import models
import schemas
from auth_utils import decode_ws_token
from connection_manager import manager
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_FORBIDDEN = 4403
WS_CLOSE_INTERNAL_ERROR = 1011


def _find_user(db: Session, username: str | None) -> models.User | None:
    if username is None:
        return None
    return db.query(models.User).filter(models.User.username == username).first()


def _is_member(db: Session, room_id: int, user_id: int) -> bool:
    membership = (
        db.query(models.RoomMember)
        .filter(models.RoomMember.room_id == room_id, models.RoomMember.user_id == user_id)
        .first()
    )
    return membership is not None


async def _send_error(websocket: WebSocket, code: str, detail: str) -> None:
    event = schemas.ErrorEvent(code=code, detail=detail)
    await websocket.send_json(event.model_dump(mode="json"))


async def _reject(websocket: WebSocket, code: int) -> None:
    # Accept before closing: a close sent before the handshake only reaches the
    # client as an HTTP 403, which hides the reason for the rejection.
    await websocket.accept()
    await websocket.close(code=code)


async def _handle_message_send(
    websocket: WebSocket,
    room_id: int,
    user: models.User,
    event: schemas.MessageSendEvent,
    db: Session,
) -> None:
    if not _is_member(db, room_id, user.id):
        await _send_error(websocket, "not_a_member", "You are not a member of this room")
        return

    message = models.Message(room_id=room_id, sender_id=user.id, content=event.content)
    db.add(message)
    db.commit()
    db.refresh(message)

    broadcast = schemas.MessageNewEvent(message=message)
    await manager.broadcast(room_id, broadcast.model_dump(mode="json"))


async def _handle_typing(
    room_id: int,
    user: models.User,
    event: schemas.TypingEvent,
) -> None:
    broadcast = schemas.TypingBroadcastEvent(
        user_id=user.id, username=user.username, is_typing=event.is_typing
    )
    await manager.broadcast(room_id, broadcast.model_dump(mode="json"))


async def _dispatch_event(
    websocket: WebSocket,
    room_id: int,
    user: models.User,
    raw_event: str,
    db: Session,
) -> None:
    try:
        payload = json.loads(raw_event)
    except json.JSONDecodeError:
        await _send_error(websocket, "invalid_json", "Event must be valid JSON")
        return

    if not isinstance(payload, dict):
        await _send_error(websocket, "invalid_event", "Event must be a JSON object")
        return

    try:
        event = schemas.CLIENT_EVENT_ADAPTER.validate_python(payload)
    except ValidationError as error:
        detail = str(error.errors()[0]["msg"])
        await _send_error(websocket, "invalid_event", detail)
        return

    if isinstance(event, schemas.MessageSendEvent):
        await _handle_message_send(websocket, room_id, user, event, db)
    else:
        await _handle_typing(room_id, user, event)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    room_id: int = Query(),
    db: Session = Depends(get_db),
):
    user = _find_user(db, decode_ws_token(token))
    if user is None:
        await _reject(websocket, WS_CLOSE_UNAUTHORIZED)
        return

    if not _is_member(db, room_id, user.id):
        await _reject(websocket, WS_CLOSE_FORBIDDEN)
        return

    await manager.connect(room_id, websocket)
    logger.info("user %s joined room %s over websocket", user.username, room_id)

    try:
        while True:
            incoming = await websocket.receive()
            if incoming["type"] == "websocket.disconnect":
                break
            text = incoming.get("text")
            if text is None:
                await _send_error(
                    websocket, "unsupported_frame", "Only text frames are supported"
                )
                continue
            try:
                await _dispatch_event(websocket, room_id, user, text, db)
            except (WebSocketDisconnect, RuntimeError):
                break
            except Exception:
                logger.exception("failed to handle event in room %s", room_id)
                await _send_error(websocket, "internal_error", "Event could not be handled")
                await websocket.close(code=WS_CLOSE_INTERNAL_ERROR)
                break
    finally:
        manager.disconnect(room_id, websocket)
        logger.info("user %s left room %s over websocket", user.username, room_id)