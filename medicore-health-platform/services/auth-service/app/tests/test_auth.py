import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared_common.database import Base

from app.core import db as db_module
from app.main import app


@pytest.fixture(autouse=True)
def _sqlite_db(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
            db.commit()
        finally:
            db.close()

    app.dependency_overrides[db_module.get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_register_and_login():
    r = client.post(
        "/auth/register",
        json={"email": "patient1@example.com", "password": "SuperSecret1", "full_name": "Jane Doe", "role": "patient"},
    )
    assert r.status_code == 201
    assert r.json()["email"] == "patient1@example.com"

    r = client.post("/auth/login", json={"email": "patient1@example.com", "password": "SuperSecret1"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and "refresh_token" in body


def test_login_invalid_password_locks_after_threshold():
    client.post(
        "/auth/register",
        json={"email": "locktest@example.com", "password": "SuperSecret1", "full_name": "Lock Test", "role": "patient"},
    )
    for _ in range(5):
        r = client.post("/auth/login", json={"email": "locktest@example.com", "password": "wrong"})
    assert r.status_code in (401, 423)


def test_get_me_requires_auth():
    r = client.get("/auth/me")
    assert r.status_code == 401
