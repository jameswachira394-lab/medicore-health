import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from shared_common.database import Base


class Patient(Base):
    """
    Owned exclusively by the Patient Service (database-per-service).
    `user_id` links back to the Authentication Service's User record.
    Sensitive fields (phone, address, insurance_details) are stored
    encrypted at the application layer (AES via shared_common.encryption)
    on top of at-rest DB/EBS encryption.
    """

    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # Encrypted at rest via application-layer encryption
    phone_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    address_encrypted: Mapped[str] = mapped_column(String(1024), nullable=False)
    emergency_contact_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    insurance_details_encrypted: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
