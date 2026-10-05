from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from dependencies import get_current_user, require_room_member

router = APIRouter(prefix="/rooms", tags=["rooms"])

DEFAULT_MESSAGE_LIMIT = 50
MAX_MESSAGE_LIMIT = 100


@router.post("", response_model=schemas.RoomOut, status_code=201)
def create_room(
    room: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_room = models.Room(name=room.name, created_by=current_user.id)
    db.add(new_room)
    db.flush()
    db.add(models.RoomMember(user_id=current_user.id, room_id=new_room.id, role="owner"))
    db.commit()
    db.refresh(new_room)
    return new_room


@router.get("", response_model=list[schemas.RoomOut])
def list_my_rooms(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Room)
        .join(models.RoomMember, models.RoomMember.room_id == models.Room.id)
        .filter(models.RoomMember.user_id == current_user.id)
        .order_by(models.Room.id)
        .all()
    )


@router.post("/{room_id}/join", response_model=schemas.RoomMemberOut)
def join_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if db.get(models.Room, room_id) is None:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = (
        db.query(models.RoomMember)
        .filter(
            models.RoomMember.room_id == room_id,
            models.RoomMember.user_id == current_user.id,
        )
        .first()
    )
    if membership is not None:
        return membership

    membership = models.RoomMember(user_id=current_user.id, room_id=room_id, role="member")
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@router.get("/{room_id}/messages", response_model=list[schemas.MessageOut])
def list_messages(
    room_id: int,
    before: int | None = Query(default=None, gt=0),
    limit: int = Query(default=DEFAULT_MESSAGE_LIMIT, ge=1, le=MAX_MESSAGE_LIMIT),
    membership: models.RoomMember = Depends(require_room_member),
    db: Session = Depends(get_db),
):
    query = db.query(models.Message).filter(
        models.Message.room_id == room_id,
        models.Message.deleted_at.is_(None),
    )

    if before is not None:
        cursor = db.get(models.Message, before)
        if cursor is None or cursor.room_id != room_id:
            raise HTTPException(status_code=400, detail="Unknown before cursor")
        query = query.filter(
            or_(
                models.Message.created_at < cursor.created_at,
                and_(
                    models.Message.created_at == cursor.created_at,
                    models.Message.id < cursor.id,
                ),
            )
        )

    return (
        query.order_by(models.Message.created_at.desc(), models.Message.id.desc())
        .limit(limit)
        .all()
    )