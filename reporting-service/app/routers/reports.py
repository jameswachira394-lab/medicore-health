from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared_common.security import make_current_user_dependency, make_require_roles

from app.core.config import settings
from app.core.db import get_db
from app.models.snapshot import DailyHospitalMetrics
from app.schemas.report import DailyMetricsOut

router = APIRouter(prefix="/reports", tags=["reporting"])
get_current_user = make_current_user_dependency(settings.JWT_SECRET, settings.JWT_ALGORITHM)
require_roles = make_require_roles(get_current_user)

ANALYTICS_ROLES = ("hospital_admin", "system_admin")


@router.get("/daily", response_model=list[DailyMetricsOut])
def get_daily_metrics(
    start: str | None = None, end: str | None = None,
    db: Session = Depends(get_db), _=Depends(require_roles(*ANALYTICS_ROLES)),
):
    query = db.query(DailyHospitalMetrics)
    if start:
        query = query.filter(DailyHospitalMetrics.metric_date >= start)
    if end:
        query = query.filter(DailyHospitalMetrics.metric_date <= end)
    return query.order_by(DailyHospitalMetrics.metric_date.desc()).limit(90).all()


@router.get("/daily/{metric_date}", response_model=DailyMetricsOut)
def get_metrics_for_date(
    metric_date: str, db: Session = Depends(get_db), _=Depends(require_roles(*ANALYTICS_ROLES))
):
    row = db.query(DailyHospitalMetrics).filter(DailyHospitalMetrics.metric_date == metric_date).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No metrics recorded for that date")
    return row


@router.post("/daily/{metric_date}/ingest", response_model=DailyMetricsOut, status_code=status.HTTP_201_CREATED)
def ingest_daily_metrics(
    metric_date: str,
    active_patients: int = 0, appointments_total: int = 0,
    appointments_completed: int = 0, appointments_cancelled: int = 0, revenue: float = 0.0,
    db: Session = Depends(get_db), _=Depends(require_roles("system_admin")),
):
    """
    Upsert endpoint used by the scheduled ETL job (e.g. an EventBridge-
    triggered Lambda or a nightly Airflow/cron task) that pulls aggregates
    from the Appointment/Billing/Patient services and writes the daily
    rollup here for fast dashboard reads.
    """
    row = db.query(DailyHospitalMetrics).filter(DailyHospitalMetrics.metric_date == metric_date).first()
    if not row:
        row = DailyHospitalMetrics(metric_date=metric_date)
        db.add(row)
    row.active_patients = active_patients
    row.appointments_total = appointments_total
    row.appointments_completed = appointments_completed
    row.appointments_cancelled = appointments_cancelled
    row.revenue = revenue
    db.flush()
    return row
