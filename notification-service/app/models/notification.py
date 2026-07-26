import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared_common.database import Base


class Channel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    event: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "appointment.booked"
    channel: Mapped[Channel] = mapped_column(Enum(Channel), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), default=NotificationStatus.QUEUED)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
