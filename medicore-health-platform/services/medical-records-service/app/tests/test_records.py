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


def _token(sub="doc-1", role="doctor"):
    return create_token(
        subject=sub, role=role, secret=config_module.settings.JWT_SECRET,
        algorithm=config_module.settings.JWT_ALGORITHM, expires_delta=timedelta(minutes=15),
    )


def test_doctor_can_add_and_read_diagnosis_with_encrypted_notes():
    r = client.post("/medical-records/entries", json={
        "patient_id": "patient-1", "doctor_id": "doc-1", "diagnosis": "Hypertension",
        "treatment": "Lifestyle change + medication", "notes": "BP 150/95, recommend follow-up in 2 weeks",
    }, headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 201
    assert r.json()["notes"] == "BP 150/95, recommend follow-up in 2 weeks"


def test_billing_role_cannot_access_medical_records():
    r = client.post("/medical-records/entries", json={
        "patient_id": "patient-1", "doctor_id": "doc-1", "diagnosis": "Hypertension",
    }, headers={"Authorization": f"Bearer {_token(sub='billing-1', role='receptionist')}"})
    assert r.status_code == 403


def test_patient_can_view_own_history_only():
    r1 = client.post("/medical-records/entries", json={
        "patient_id": "patient-1", "doctor_id": "doc-1", "diagnosis": "Flu",
    }, headers={"Authorization": f"Bearer {_token()}"})
    assert r1.status_code == 201

    patient_token = _token(sub="patient-1", role="patient")
    r2 = client.get("/medical-records/patients/patient-1/history", headers={"Authorization": f"Bearer {patient_token}"})
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    other_patient_token = _token(sub="patient-2", role="patient")
    r3 = client.get("/medical-records/patients/patient-1/history", headers={"Authorization": f"Bearer {other_patient_token}"})
    assert r3.status_code == 403
