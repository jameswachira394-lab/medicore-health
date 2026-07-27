import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared_common.database import Base
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


def test_receive_event_fans_out_to_all_channels():
    r = client.post("/notifications/events", json={
        "event": "appointment.booked", "appointment_id": "appt-1",
        "patient_id": "patient-1", "doctor_id": "doc-1", "scheduled_start": "2026-08-01T10:00:00Z",
    })
    assert r.status_code == 202
