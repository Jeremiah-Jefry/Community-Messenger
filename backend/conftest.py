import os

# Must be set before config/main are imported, so the app never touches the
# developer database (messenger.db) while tests run.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-used-anywhere-else-0123456789")
os.environ["SQLALCHEMY_DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from main import app, get_db

TEST_USER = {"username": "test_user", "password": "test-password-1"}


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def register_user(client, user=TEST_USER):
    response = client.post("/register", json=user)
    assert response.status_code == 200, response.text
    return response.json()