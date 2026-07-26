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


def _token(sub="staff-1", role="receptionist"):
    return create_token(
        subject=sub, role=role, secret=config_module.settings.JWT_SECRET,
        algorithm=config_module.settings.JWT_ALGORITHM, expires_delta=timedelta(minutes=15),
    )


def test_create_invoice_and_pay():
    r = client.post("/billing/invoices", json={
        "patient_id": "patient-1",
        "line_items": [{"description": "Consultation", "amount": 50}, {"description": "Lab test", "amount": 30}],
    }, headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 201
    invoice = r.json()
    assert invoice["total_amount"] == 80
    assert invoice["status"] == "pending"

    r2 = client.post(f"/billing/invoices/{invoice['id']}/payments", json={
        "amount": 80, "method": "card", "reference": "txn_123",
    }, headers={"Authorization": f"Bearer {_token(sub='patient-1', role='patient')}"})
    assert r2.status_code == 201
    assert r2.json()["status"] == "paid"


def test_doctor_cannot_access_billing():
    r = client.post("/billing/invoices", json={
        "patient_id": "patient-1", "line_items": [{"description": "Consultation", "amount": 50}],
    }, headers={"Authorization": f"Bearer {_token(sub='doc-1', role='doctor')}"})
    assert r.status_code == 403
