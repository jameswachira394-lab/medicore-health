from datetime import datetime

from pydantic import BaseModel

from app.models.notification import Channel, NotificationStatus


class AppointmentEvent(BaseModel):
    event: str
    appointment_id: str
    patient_id: str
    doctor_id: str
    scheduled_start: str


class NotificationLogOut(BaseModel):
    id: str
    recipient_user_id: str
    event: str
    channel: Channel
    status: NotificationStatus
    created_at: datetime

    class Config:
        from_attributes = True
