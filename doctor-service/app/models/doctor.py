import uuid
from datetime import datetime, time, timezone

from sqlalchemy import DateTime, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from shared_common.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    license_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class DoctorAvailability(Base):
    """A recurring weekly availability block, e.g. Monday 09:00-13:00."""

    __tablename__ = "doctor_availability"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
