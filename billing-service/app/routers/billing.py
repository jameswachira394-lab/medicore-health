from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from shared_common.audit import write_audit_log
from shared_common.security import make_current_user_dependency, make_require_roles

from app.core.config import settings
from app.core.db import get_db
from app.models.billing import Invoice, InvoiceLineItem, InvoiceStatus, InsuranceClaim, Payment
from app.schemas.billing import (
    InsuranceClaimCreate,
    InsuranceClaimOut,
    InvoiceCreate,
    InvoiceOut,
    PaymentCreate,
)

router = APIRouter(prefix="/billing", tags=["billing"])
get_current_user = make_current_user_dependency(settings.JWT_SECRET, settings.JWT_ALGORITHM)
require_roles = make_require_roles(get_current_user)

BILLING_STAFF = ("receptionist", "hospital_admin", "system_admin")


def _authorize(current_user, patient_id: str):
    if current_user.role == "patient" and current_user.sub != patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access another patient's invoices")
    if current_user.role not in ("patient", *BILLING_STAFF):
        # Doctors/nurses explicitly excluded: "Doctor can view assigned
        # patients, cannot view billing" per the access-control requirement.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted to access billing")


@router.post("/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate, request: Request, db: Session = Depends(get_db),
    current_user=Depends(require_roles(*BILLING_STAFF)),
):
    total = sum(item.amount for item in payload.line_items)
    invoice = Invoice(patient_id=payload.patient_id, appointment_id=payload.appointment_id, total_amount=total)
    invoice.line_items = [InvoiceLineItem(description=i.description, amount=i.amount) for i in payload.line_items]
    db.add(invoice)
    db.flush()

    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="CREATE",
        resource_type="Invoice", resource_id=invoice.id,
        source_ip=request.client.host if request.client else None,
    )
    return invoice


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    _authorize(current_user, invoice.patient_id)
    return invoice


@router.get("/patients/{patient_id}/invoices", response_model=list[InvoiceOut])
def list_patient_invoices(patient_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _authorize(current_user, patient_id)
    return db.query(Invoice).filter(Invoice.patient_id == patient_id).all()


@router.post("/invoices/{invoice_id}/payments", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def record_payment(
    invoice_id: str, payload: PaymentCreate, request: Request, db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    _authorize(current_user, invoice.patient_id)

    payment = Payment(invoice_id=invoice.id, amount=payload.amount, method=payload.method, reference=payload.reference)
    db.add(payment)
    invoice.amount_paid += payload.amount
    invoice.status = InvoiceStatus.PAID if invoice.amount_paid >= invoice.total_amount else InvoiceStatus.PARTIALLY_PAID
    db.flush()

    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="PAYMENT",
        resource_type="Invoice", resource_id=invoice.id,
        source_ip=request.client.host if request.client else None,
        metadata={"amount": payload.amount, "method": payload.method.value},
    )
    return invoice


@router.post("/insurance-claims", response_model=InsuranceClaimOut, status_code=status.HTTP_201_CREATED)
def submit_insurance_claim(
    payload: InsuranceClaimCreate, db: Session = Depends(get_db), _=Depends(require_roles(*BILLING_STAFF))
):
    invoice = db.query(Invoice).filter(Invoice.id == payload.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    claim = InsuranceClaim(**payload.model_dump())
    db.add(claim)
    db.flush()
    return claim
