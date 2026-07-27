from datetime import datetime

from pydantic import BaseModel, Field

from app.models.billing import InvoiceStatus, PaymentMethod


class LineItemIn(BaseModel):
    description: str
    amount: float = Field(gt=0)


class InvoiceCreate(BaseModel):
    patient_id: str
    appointment_id: str | None = None
    line_items: list[LineItemIn]


class LineItemOut(BaseModel):
    id: str
    description: str
    amount: float

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    id: str
    amount: float
    method: PaymentMethod
    reference: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    id: str
    patient_id: str
    appointment_id: str | None
    total_amount: float
    amount_paid: float
    status: InvoiceStatus
    line_items: list[LineItemOut]
    payments: list[PaymentOut]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    method: PaymentMethod
    reference: str | None = None


class InsuranceClaimCreate(BaseModel):
    invoice_id: str
    insurer_name: str
    policy_number: str
    claim_amount: float = Field(gt=0)


class InsuranceClaimOut(BaseModel):
    id: str
    invoice_id: str
    insurer_name: str
    policy_number: str
    claim_amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
