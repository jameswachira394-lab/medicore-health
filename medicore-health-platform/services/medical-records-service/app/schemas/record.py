from datetime import datetime

from pydantic import BaseModel


class RecordEntryCreate(BaseModel):
    patient_id: str
    doctor_id: str
    appointment_id: str | None = None
    diagnosis: str
    treatment: str | None = None
    notes: str | None = None


class RecordEntryOut(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    appointment_id: str | None
    diagnosis: str
    treatment: str | None
    notes: str | None
    created_at: datetime


class PrescriptionCreate(BaseModel):
    record_entry_id: str
    patient_id: str
    doctor_id: str
    medication: str
    dosage: str
    instructions: str | None = None


class PrescriptionOut(BaseModel):
    id: str
    record_entry_id: str
    patient_id: str
    doctor_id: str
    medication: str
    dosage: str
    instructions: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class LabTestCreate(BaseModel):
    record_entry_id: str
    patient_id: str
    doctor_id: str
    test_name: str


class LabTestResultUpdate(BaseModel):
    status: str
    result: str | None = None


class LabTestOut(BaseModel):
    id: str
    record_entry_id: str
    patient_id: str
    doctor_id: str
    test_name: str
    status: str
    result: str | None
    created_at: datetime
