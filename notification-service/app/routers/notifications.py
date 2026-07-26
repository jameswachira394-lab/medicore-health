import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from shared_common.security import make_current_user_dependency

from app.core.config import settings
from app.core.db import get_db
from app.models.notification import Channel, NotificationLog, NotificationStatus
from app.schemas.notification import AppointmentEvent, NotificationLogOut
from app.services.senders import send_email, send_push, send_sms

router = APIRouter(prefix="/notifications", tags=["notifications"])
get_current_user = make_current_user_dependency(settings.JWT_SECRET, settings.JWT_ALGORITHM)


@router.post("/events", status_code=202)
def receive_event(event: AppointmentEvent, db: Session = Depends(get_db)):
    """
    Internal endpoint called by other microservices (e.g. Appointment
    Service) when a domain event occurs. Fans the event out across all
    channels. In the event-driven variant of the architecture this endpoint
    is replaced by a Kafka/SQS consumer, but the fan-out logic is identical.
    """
    payload_json = event.model_dump_json()

    for channel, sender in (
        (Channel.EMAIL, lambda: send_email(f"{event.patient_id}@patients.medicore.health", event.event, payload_json)),
        (Channel.SMS, lambda: send_sms(event.patient_id, f"{event.event} at {event.scheduled_start}")),
        (Channel.PUSH, lambda: send_push(event.patient_id, event.event, "Tap for details")),
    ):
        ok = sender()
        db.add(
            NotificationLog(
                recipient_user_id=event.patient_id,
                event=event.event,
                channel=channel,
                status=NotificationStatus.SENT if ok else NotificationStatus.FAILED,
                payload=payload_json,
            )
        )
    return {"message": "notification dispatched"}


@router.get("/users/{user_id}/logs", response_model=list[NotificationLogOut])
def get_logs(user_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(NotificationLog).filter(NotificationLog.recipient_user_id == user_id)
    return query.order_by(NotificationLog.created_at.desc()).limit(50).all()
