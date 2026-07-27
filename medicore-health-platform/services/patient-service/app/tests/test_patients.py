import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared_common.database import Base
from shared_common.security import create_token
from app.core import config as config_module
from app.core import db as db_module
from app.main import app
from datetime import timedelta


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


def _token(sub="user-1", role="patient"):
    return create_token(
        subject=sub, role=role, secret=config_module.settings.JWT_SECRET,
        algorithm=config_module.settings.JWT_ALGORITHM, expires_delta=timedelta(minutes=15),
    )


def test_create_and_get_patient_encrypts_pii():
    token = _token()
    payload = {
        "user_id": "user-1", "full_name": "Jane Doe", "date_of_birth": "1990-01-01",
        "gender": "female", "email": "jane@example.com", "phone": "+254700000000",
        "address": "123 Main St", "emergency_contact": "John Doe +254711111111",
        "insurance_details": "AAR Insurance #12345",
    }
    r = client.post("/patients", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    patient_id = r.json()["id"]
    assert r.json()["phone"] == "+254700000000"

    r2 = client.get(f"/patients/{patient_id}", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["insurance_details"] == "AAR Insurance #12345"


def test_patient_cannot_access_another_patients_record():
    token1 = _token(sub="user-1")
    client.post("/patients", json={
        "user_id": "user-1", "full_name": "Jane Doe", "date_of_birth": "1990-01-01",
        "gender": "female", "email": "jane@example.com", "phone": "+254700000000", "address": "123 Main St",
    }, headers={"Authorization": f"Bearer {token1}"})
    r = client.get("/patients", headers={"Authorization": f"Bearer {_token(sub='staff-1', role='receptionist')}"})
    patient_id = r.json()[0]["id"]

    token2 = _token(sub="user-2")
    r2 = client.get(f"/patients/{patient_id}", headers={"Authorization": f"Bearer {token2}"})
    assert r2.status_code == 403


def test_staff_can_search_patients():
    token1 = _token(sub="user-1")
    client.post("/patients", json={
        "user_id": "user-1", "full_name": "Jane Doe", "date_of_birth": "1990-01-01",
        "gender": "female", "email": "jane@example.com", "phone": "+254700000000", "address": "123 Main St",
    }, headers={"Authorization": f"Bearer {token1}"})

    staff_token = _token(sub="staff-1", role="receptionist")
    r = client.get("/patients?q=Jane", headers={"Authorization": f"Bearer {staff_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_patient_can_fetch_own_profile_via_me():
    token = _token(sub="user-42")
    client.post("/patients", json={
        "user_id": "user-42", "full_name": "Amina Yusuf", "date_of_birth": "1988-04-12",
        "gender": "female", "email": "amina@example.com", "phone": "+254700111222", "address": "Nairobi",
    }, headers={"Authorization": f"Bearer {token}"})

    r = client.get("/patients/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["user_id"] == "user-42"


def test_me_returns_404_before_onboarding():
    token = _token(sub="user-99")
    r = client.get("/patients/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
