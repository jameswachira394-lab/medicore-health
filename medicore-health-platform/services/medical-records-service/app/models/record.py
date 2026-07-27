import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared_common.database import Base


class MedicalRecordEntry(Base):
    """
    One entry in a patient's medical history: a diagnosis, with its
    treatment and (optional) prescription, tied to a specific appointment.
    `notes_encrypted` holds free-text clinical notes, encrypted at the
    application layer as required for the most sensitive service in the
    platform. Access is restricted to clinical roles only — billing staff
    must never be able to read diagnosis/notes (see access-control matrix).
    """

    __tablename__ = "medical_record_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    appointment_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)

    diagnosis: Mapped[str] = mapped_column(String(500), nullable=False)
    treatment: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_entry_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    medication: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class LabTestRequest(Base):
    __tablename__ = "lab_test_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_entry_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="requested")  # requested | in_progress | completed
    result_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
