from datetime import date, datetime

from pydantic import BaseModel, EmailStr


class PatientCreate(BaseModel):
    user_id: str
    full_name: str
    date_of_birth: date
    gender: str
    email: EmailStr
    phone: str
    address: str
    emergency_contact: str | None = None
    insurance_details: str | None = None


class PatientUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    insurance_details: str | None = None


class PatientOut(BaseModel):
    id: str
    user_id: str
    full_name: str
    date_of_birth: date
    gender: str
    email: EmailStr
    phone: str
    address: str
    emergency_contact: str | None
    insurance_details: str | None
    created_at: datetime
    updated_at: datetime
