from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from shared_common.audit import write_audit_log
from shared_common.encryption import decrypt_field, encrypt_field
from shared_common.security import make_current_user_dependency, make_require_roles

from app.core.config import settings
from app.core.db import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientOut, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])
get_current_user = make_current_user_dependency(settings.JWT_SECRET, settings.JWT_ALGORITHM)
require_roles = make_require_roles(get_current_user)

STAFF_ROLES = ("receptionist", "doctor", "nurse", "hospital_admin", "system_admin")


def _to_out(p: Patient) -> PatientOut:
    return PatientOut(
        id=p.id, user_id=p.user_id, full_name=p.full_name, date_of_birth=p.date_of_birth,
        gender=p.gender, email=p.email,
        phone=decrypt_field(p.phone_encrypted),
        address=decrypt_field(p.address_encrypted),
        emergency_contact=decrypt_field(p.emergency_contact_encrypted) if p.emergency_contact_encrypted else None,
        insurance_details=decrypt_field(p.insurance_details_encrypted) if p.insurance_details_encrypted else None,
        created_at=p.created_at, updated_at=p.updated_at,
    )


def _authorize_patient_access(current_user, patient: Patient):
    """Patients may only access their own record; staff roles may access any."""
    if current_user.role == "patient" and current_user.sub != patient.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access another patient's record")


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate, request: Request, db: Session = Depends(get_db),
    current_user=Depends(require_roles("patient", *STAFF_ROLES)),
):
    existing = db.query(Patient).filter(Patient.user_id == payload.user_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient profile already exists")

    patient = Patient(
        user_id=payload.user_id, full_name=payload.full_name, date_of_birth=payload.date_of_birth,
        gender=payload.gender, email=payload.email,
        phone_encrypted=encrypt_field(payload.phone),
        address_encrypted=encrypt_field(payload.address),
        emergency_contact_encrypted=encrypt_field(payload.emergency_contact) if payload.emergency_contact else None,
        insurance_details_encrypted=encrypt_field(payload.insurance_details) if payload.insurance_details else None,
    )
    db.add(patient)
    db.flush()

    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="CREATE",
        resource_type="Patient", resource_id=patient.id,
        source_ip=request.client.host if request.client else None,
    )
    return _to_out(patient)


@router.get("/me", response_model=PatientOut)
def get_my_patient_profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Lets a patient fetch their own record without knowing its internal id —
    the frontend calls this right after login to discover `patient.id`
    (needed for booking appointments, viewing records/invoices, etc.).
    404 signals "onboarding not completed yet" to the frontend.
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.sub).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return _to_out(patient)


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: str, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    _authorize_patient_access(current_user, patient)

    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="READ",
        resource_type="Patient", resource_id=patient.id,
        source_ip=request.client.host if request.client else None,
    )
    return _to_out(patient)


@router.patch("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: str, payload: PatientUpdate, request: Request,
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    _authorize_patient_access(current_user, patient)

    if payload.full_name is not None:
        patient.full_name = payload.full_name
    if payload.phone is not None:
        patient.phone_encrypted = encrypt_field(payload.phone)
    if payload.address is not None:
        patient.address_encrypted = encrypt_field(payload.address)
    if payload.emergency_contact is not None:
        patient.emergency_contact_encrypted = encrypt_field(payload.emergency_contact)
    if payload.insurance_details is not None:
        patient.insurance_details_encrypted = encrypt_field(payload.insurance_details)

    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="UPDATE",
        resource_type="Patient", resource_id=patient.id,
        source_ip=request.client.host if request.client else None,
    )
    return _to_out(patient)


@router.get("", response_model=list[PatientOut])
def search_patients(
    q: str | None = None, db: Session = Depends(get_db),
    current_user=Depends(require_roles(*STAFF_ROLES)),
):
    """Staff-only patient search by name or email."""
    query = db.query(Patient)
    if q:
        query = query.filter(Patient.full_name.ilike(f"%{q}%") | Patient.email.ilike(f"%{q}%"))
    return [_to_out(p) for p in query.limit(50).all()]
