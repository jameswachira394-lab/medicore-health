from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from shared_common.audit import write_audit_log
from shared_common.security import make_current_user_dependency, make_require_roles

from app.core.config import settings
from app.core.db import get_db
from app.models.appointment import Appointment, AppointmentStatus, WaitlistEntry
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentReschedule,
    WaitlistCreate,
    WaitlistOut,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])
get_current_user = make_current_user_dependency(settings.JWT_SECRET, settings.JWT_ALGORITHM)
require_roles = make_require_roles(get_current_user)


def _overlaps(db: Session, doctor_id: str, start: datetime, end: datetime) -> bool:
    """
    Reserve-slot check: true if the doctor already has a CONFIRMED or
    REQUESTED appointment overlapping [start, end).
    """
    clash = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_([AppointmentStatus.REQUESTED, AppointmentStatus.CONFIRMED]),
            and_(Appointment.scheduled_start < end, Appointment.scheduled_end > start),
        )
        .first()
    )
    return clash is not None


async def _notify(event: str, appointment: Appointment) -> None:
    """
    Fire-and-forget call to the Notification Service. Failures are swallowed
    (logged) so a notification outage never blocks the booking workflow —
    in production this would instead publish to an event bus (Kafka/SNS)
    per the event-driven architecture section of the platform design.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/notifications/events",
                json={
                    "event": event,
                    "appointment_id": appointment.id,
                    "patient_id": appointment.patient_id,
                    "doctor_id": appointment.doctor_id,
                    "scheduled_start": appointment.scheduled_start.isoformat(),
                },
            )
    except httpx.HTTPError:
        pass


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    payload: AppointmentCreate, request: Request, db: Session = Depends(get_db),
    current_user=Depends(require_roles("patient", "receptionist", "doctor", "nurse")),
):
    if payload.scheduled_start < datetime.now(timezone.utc) and not payload.is_emergency:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot book an appointment in the past")

    if _overlaps(db, payload.doctor_id, payload.scheduled_start, payload.scheduled_end):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Doctor is not available at that time")

    appointment = Appointment(
        **payload.model_dump(),
        status=AppointmentStatus.CONFIRMED if payload.is_emergency else AppointmentStatus.REQUESTED,
    )
    db.add(appointment)
    db.flush()

    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="CREATE",
        resource_type="Appointment", resource_id=appointment.id,
        source_ip=request.client.host if request.client else None,
    )
    await _notify("appointment.booked", appointment)
    return appointment


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if current_user.role == "patient" and current_user.sub != appt.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")
    if current_user.role == "doctor" and current_user.sub != appt.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")
    return appt


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    patient_id: str | None = None, doctor_id: str | None = None,
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    query = db.query(Appointment)
    if current_user.role == "patient":
        query = query.filter(Appointment.patient_id == current_user.sub)
    elif current_user.role == "doctor":
        query = query.filter(Appointment.doctor_id == current_user.sub)
    else:
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)
    return query.order_by(Appointment.scheduled_start).limit(100).all()


@router.post("/{appointment_id}/confirm", response_model=AppointmentOut)
def confirm_appointment(
    appointment_id: str, db: Session = Depends(get_db),
    _=Depends(require_roles("doctor", "receptionist", "hospital_admin")),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    appt.status = AppointmentStatus.CONFIRMED
    return appt


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: str, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if current_user.role == "patient" and current_user.sub != appt.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")
    appt.status = AppointmentStatus.CANCELLED

    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="CANCEL",
        resource_type="Appointment", resource_id=appt.id,
        source_ip=request.client.host if request.client else None,
    )
    return appt


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule_appointment(
    appointment_id: str, payload: AppointmentReschedule, db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if current_user.role == "patient" and current_user.sub != appt.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")

    others_overlap = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == appt.doctor_id,
            Appointment.id != appt.id,
            Appointment.status.in_([AppointmentStatus.REQUESTED, AppointmentStatus.CONFIRMED]),
            and_(Appointment.scheduled_start < payload.scheduled_end, Appointment.scheduled_end > payload.scheduled_start),
        )
        .first()
    )
    if others_overlap:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Doctor is not available at the new time")

    appt.scheduled_start = payload.scheduled_start
    appt.scheduled_end = payload.scheduled_end
    appt.status = AppointmentStatus.REQUESTED
    return appt


@router.post("/waitlist", response_model=WaitlistOut, status_code=status.HTTP_201_CREATED)
def join_waitlist(
    payload: WaitlistCreate, db: Session = Depends(get_db), _=Depends(require_roles("patient", "receptionist"))
):
    entry = WaitlistEntry(**payload.model_dump())
    db.add(entry)
    db.flush()
    return entry
