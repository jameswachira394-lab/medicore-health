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


def _token(role="system_admin"):
    return create_token(
        subject="admin-1", role=role, secret=config_module.settings.JWT_SECRET,
        algorithm=config_module.settings.JWT_ALGORITHM, expires_delta=timedelta(minutes=15),
    )


def test_ingest_and_read_daily_metrics():
    r = client.post("/reports/daily/2026-07-25/ingest?active_patients=120&appointments_total=45&appointments_completed=40&appointments_cancelled=5&revenue=3200.5",
                     headers={"Authorization": f"Bearer {_token()}"})
    assert r.status_code == 201

    r2 = client.get("/reports/daily/2026-07-25", headers={"Authorization": f"Bearer {_token(role='hospital_admin')}"})
    assert r2.status_code == 200
    assert r2.json()["appointments_total"] == 45


def test_patient_role_cannot_view_reports():
    r = client.get("/reports/daily", headers={"Authorization": f"Bearer {_token(role='patient')}"})
    assert r.status_code == 403
