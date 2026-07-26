import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
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


@pytest.fixture(autouse=True)
def _mock_notify():
    with patch("app.routers.appointments._notify", new=AsyncMock(return_value=None)):
        yield


client = TestClient(app)


def _token(sub="patient-1", role="patient"):
    return create_token(
        subject=sub, role=role, secret=config_module.settings.JWT_SECRET,
        algorithm=config_module.settings.JWT_ALGORITHM, expires_delta=timedelta(minutes=15),
    )


def _future(hours=48):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def test_book_appointment():
    r = client.post("/appointments", json={
        "patient_id": "patient-1", "doctor_id": "doctor-1",
        "scheduled_start": _future(48), "scheduled_end": _future(49), "reason": "Checkup",
    }, headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 201
    assert r.json()["status"] == "requested"


def test_double_booking_rejected():
    payload = {
        "patient_id": "patient-1", "doctor_id": "doctor-1",
        "scheduled_start": _future(48), "scheduled_end": _future(49),
    }
    r1 = client.post("/appointments", json=payload, headers={"Authorization": f"Bearer {_token()}"})
    assert r1.status_code == 201

    payload2 = dict(payload, patient_id="patient-2")
    r2 = client.post("/appointments", json=payload2, headers={"Authorization": f"Bearer {_token(sub='patient-2')}"})
    assert r2.status_code == 409


def test_patient_cannot_view_others_appointment():
    r1 = client.post("/appointments", json={
        "patient_id": "patient-1", "doctor_id": "doctor-1",
        "scheduled_start": _future(48), "scheduled_end": _future(49),
    }, headers={"Authorization": f"Bearer {_token()}"})
    appt_id = r1.json()["id"]

    r2 = client.get(f"/appointments/{appt_id}", headers={"Authorization": f"Bearer {_token(sub='patient-2')}"})
    assert r2.status_code == 403


def test_cancel_appointment():
    r1 = client.post("/appointments", json={
        "patient_id": "patient-1", "doctor_id": "doctor-1",
        "scheduled_start": _future(48), "scheduled_end": _future(49),
    }, headers={"Authorization": f"Bearer {_token()}"})
    appt_id = r1.json()["id"]

    r2 = client.post(f"/appointments/{appt_id}/cancel", headers={"Authorization": f"Bearer {_token()}"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "cancelled"
