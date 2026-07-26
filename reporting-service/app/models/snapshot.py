import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared_common.database import Base


class DailyHospitalMetrics(Base):
    """
    A materialized daily rollup, refreshed by a scheduled job that reads
    from the other services (or, in the event-driven variant, built
    incrementally as events land on the Kafka/SQS bus). This lets the
    Reporting Service answer dashboard queries fast without hammering
    the operational databases of other services on every request.
    """

    __tablename__ = "daily_hospital_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_date: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)  # YYYY-MM-DD

    active_patients: Mapped[int] = mapped_column(Integer, default=0)
    appointments_total: Mapped[int] = mapped_column(Integer, default=0)
    appointments_completed: Mapped[int] = mapped_column(Integer, default=0)
    appointments_cancelled: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
