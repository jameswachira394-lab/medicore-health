import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared_common.database import Base
from shared_common.security import create_token
from app.core import config as config_module
from app.core import db as db_module
from app.main import app


@pytest.fixture(autouse=True)
def _sqlite_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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


def _token(sub="admin-1", role="hospital_admin"):
    return create_token(
        subject=sub, role=role, secret=config_module.settings.JWT_SECRET,
        algorithm=config_module.settings.JWT_ALGORITHM, expires_delta=timedelta(minutes=15),
    )


def test_add_doctor_requires_admin():
    r = client.post("/doctors", json={
        "user_id": "doc-user-1", "full_name": "Dr. Smith", "specialization": "Cardiology",
        "department": "Cardiology", "license_number": "LIC-001",
    }, headers={"Authorization": f"Bearer {_token(role='patient')}"})
    assert r.status_code == 403


def test_add_and_search_doctor():
    r = client.post("/doctors", json={
        "user_id": "doc-user-1", "full_name": "Dr. Smith", "specialization": "Cardiology",
        "department": "Cardiology", "license_number": "LIC-001",
    }, headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 201
    doctor_id = r.json()["id"]

    r2 = client.get("/doctors?specialization=Cardio", headers={"Authorization": f"Bearer {_token(role='patient')}"})
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    r3 = client.post(f"/doctors/{doctor_id}/availability", json={
        "day_of_week": 0, "start_time": "09:00:00", "end_time": "13:00:00",
    }, headers={"Authorization": f"Bearer {_token()}"})
    assert r3.status_code == 201


def test_doctor_can_fetch_own_profile_via_me():
    client.post("/doctors", json={
        "user_id": "doc-user-99", "full_name": "Dr. Amara", "specialization": "Pediatrics",
        "department": "Pediatrics", "license_number": "LIC-099",
    }, headers={"Authorization": f"Bearer {_token()}"})

    doc_token = _token(sub="doc-user-99", role="doctor")
    r = client.get("/doctors/me", headers={"Authorization": f"Bearer {doc_token}"})
    assert r.status_code == 200
    assert r.json()["user_id"] == "doc-user-99"


def test_me_404_when_no_profile_linked():
    r = client.get("/doctors/me", headers={"Authorization": f"Bearer {_token(sub='unlinked-user', role='doctor')}"})
    assert r.status_code == 404
