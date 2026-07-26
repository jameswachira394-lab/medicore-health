from datetime import datetime, time

from pydantic import BaseModel, field_validator


class DoctorCreate(BaseModel):
    user_id: str
    full_name: str
    specialization: str
    department: str
    license_number: str
    years_experience: int = 0


class DoctorOut(BaseModel):
    id: str
    user_id: str
    full_name: str
    specialization: str
    department: str
    license_number: str
    years_experience: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AvailabilityCreate(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time

    @field_validator("day_of_week")
    @classmethod
    def validate_dow(cls, v):
        if not 0 <= v <= 6:
            raise ValueError("day_of_week must be between 0 (Monday) and 6 (Sunday)")
        return v


class AvailabilityOut(BaseModel):
    id: str
    doctor_id: str
    day_of_week: int
    start_time: time
    end_time: time

    class Config:
        from_attributes = True
