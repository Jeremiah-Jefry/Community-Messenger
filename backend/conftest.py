import os
from datetime import timedelta
from pathlib import Path

# Must be set before config/main are imported, so the app never touches the
# developer database (messenger.db) while tests run.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-used-anywhere-else-0123456789")
os.environ["SQLALCHEMY_DATABASE_URL"] = "sqlite://"

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import get_db
from main import app

BACKEND_DIR = Path(__file__).resolve().parent
TEST_USER = {"username": "test_user", "password": "test-password-1"}
OTHER_USER = {"username": "other_user", "password": "other-password-1"}


@pytest.fixture(scope="session")
def test_engine():
    # In-memory SQLite shared between threads. The schema comes from the
    # Alembic migrations, so tests exercise them as well.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    alembic_config = AlembicConfig(str(BACKEND_DIR / "alembic.ini"))
    with engine.begin() as connection:
        alembic_config.attributes["connection"] = connection
        command.upgrade(alembic_config, "head")
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory):
    clear_tables(session_factory)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def clear_tables(session_factory):
    with session_factory() as session:
        session.query(models.Message).delete()
        session.query(models.RoomMember).delete()
        session.query(models.Room).delete()
        session.query(models.User).delete()
        session.commit()


def register_user(client, user=TEST_USER):
    response = client.post("/register", json=user)
    assert response.status_code == 200, response.text
    return response.json()


def login(client, user=TEST_USER):
    response = client.post(
        "/login", data={"username": user["username"], "password": user["password"]}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def ws_token(client, user=TEST_USER):
    response = client.post(
        "/login", data={"username": user["username"], "password": user["password"]}
    )
    assert response.status_code == 200, response.text
    return response.json()["ws_token"]


def auth_header(client, user=TEST_USER):
    return {"Authorization": f"Bearer {login(client, user)}"}


def create_room(client, headers, name="General"):
    response = client.post("/rooms", json={"name": name}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def join_room(client, room_id, headers):
    return client.post(f"/rooms/{room_id}/join", headers=headers)


def connect_socket(client, token, room_id):
    return client.websocket_connect(f"/ws?token={token}&room_id={room_id}")


def seed_messages(db, room_id, sender_id, count):
    base = models.utcnow() - timedelta(days=1)
    messages = [
        models.Message(
            room_id=room_id,
            sender_id=sender_id,
            content=f"message {index}",
            created_at=base + timedelta(seconds=index),
        )
        for index in range(count)
    ]
    db.add_all(messages)
    db.commit()
    for message in messages:
        db.refresh(message)
    return messages