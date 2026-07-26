from datetime import datetime

from pydantic import BaseModel, model_validator

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    patient_id: str
    doctor_id: str
    scheduled_start: datetime
    scheduled_end: datetime
    reason: str | None = None
    is_emergency: bool = False

    @model_validator(mode="after")
    def check_times(self):
        if self.scheduled_end <= self.scheduled_start:
            raise ValueError("scheduled_end must be after scheduled_start")
        return self


class AppointmentOut(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    scheduled_start: datetime
    scheduled_end: datetime
    status: AppointmentStatus
    reason: str | None
    is_emergency: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppointmentReschedule(BaseModel):
    scheduled_start: datetime
    scheduled_end: datetime


class WaitlistCreate(BaseModel):
    patient_id: str
    doctor_id: str
    preferred_date: datetime


class WaitlistOut(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    preferred_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True
