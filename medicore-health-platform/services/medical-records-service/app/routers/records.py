from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from shared_common.audit import write_audit_log
from shared_common.encryption import decrypt_field, encrypt_field
from shared_common.security import make_current_user_dependency, make_require_roles

from app.core.config import settings
from app.core.db import get_db
from app.models.record import LabTestRequest, MedicalRecordEntry, Prescription
from app.schemas.record import (
    LabTestCreate,
    LabTestOut,
    LabTestResultUpdate,
    PrescriptionCreate,
    PrescriptionOut,
    RecordEntryCreate,
    RecordEntryOut,
)

router = APIRouter(prefix="/medical-records", tags=["medical-records"])
get_current_user = make_current_user_dependency(settings.JWT_SECRET, settings.JWT_ALGORITHM)
require_roles = make_require_roles(get_current_user)

# Only clinical roles may touch this service at all. Billing/receptionist
# roles are deliberately excluded platform-wide per the access-control
# requirement: "Billing can view payments, cannot view medical notes."
CLINICAL_ROLES = ("doctor", "nurse", "hospital_admin", "system_admin")


def _entry_to_out(e: MedicalRecordEntry) -> RecordEntryOut:
    return RecordEntryOut(
        id=e.id, patient_id=e.patient_id, doctor_id=e.doctor_id, appointment_id=e.appointment_id,
        diagnosis=e.diagnosis, treatment=e.treatment,
        notes=decrypt_field(e.notes_encrypted) if e.notes_encrypted else None,
        created_at=e.created_at,
    )


def _authorize(current_user, patient_id: str, doctor_id: str | None = None):
    if current_user.role == "patient":
        if current_user.sub != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access another patient's records")
    elif current_user.role not in CLINICAL_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted to access medical records")


@router.post("/entries", response_model=RecordEntryOut, status_code=status.HTTP_201_CREATED)
def add_entry(
    payload: RecordEntryCreate, request: Request, db: Session = Depends(get_db),
    current_user=Depends(require_roles("doctor", "hospital_admin", "system_admin")),
):
    entry = MedicalRecordEntry(
        patient_id=payload.patient_id, doctor_id=payload.doctor_id, appointment_id=payload.appointment_id,
        diagnosis=payload.diagnosis, treatment=payload.treatment,
        notes_encrypted=encrypt_field(payload.notes) if payload.notes else None,
    )
    db.add(entry)
    db.flush()

    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="CREATE",
        resource_type="MedicalRecordEntry", resource_id=entry.id,
        source_ip=request.client.host if request.client else None,
    )
    return _entry_to_out(entry)


@router.get("/entries/{entry_id}", response_model=RecordEntryOut)
def get_entry(entry_id: str, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    entry = db.query(MedicalRecordEntry).filter(MedicalRecordEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    _authorize(current_user, entry.patient_id)

    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="READ",
        resource_type="MedicalRecordEntry", resource_id=entry.id,
        source_ip=request.client.host if request.client else None,
    )
    return _entry_to_out(entry)


@router.get("/patients/{patient_id}/history", response_model=list[RecordEntryOut])
def patient_history(
    patient_id: str, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    _authorize(current_user, patient_id)
    entries = (
        db.query(MedicalRecordEntry)
        .filter(MedicalRecordEntry.patient_id == patient_id)
        .order_by(MedicalRecordEntry.created_at.desc())
        .all()
    )
    write_audit_log(
        actor_id=current_user.sub, actor_role=current_user.role, action="READ",
        resource_type="PatientHistory", resource_id=patient_id,
        source_ip=request.client.host if request.client else None,
    )
    return [_entry_to_out(e) for e in entries]


@router.post("/prescriptions", response_model=PrescriptionOut, status_code=status.HTTP_201_CREATED)
def create_prescription(
    payload: PrescriptionCreate, db: Session = Depends(get_db),
    _=Depends(require_roles("doctor")),
):
    rx = Prescription(**payload.model_dump())
    db.add(rx)
    db.flush()
    return rx


@router.get("/patients/{patient_id}/prescriptions", response_model=list[PrescriptionOut])
def list_prescriptions(patient_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _authorize(current_user, patient_id)
    return db.query(Prescription).filter(Prescription.patient_id == patient_id).all()


@router.post("/lab-tests", response_model=LabTestOut, status_code=status.HTTP_201_CREATED)
def request_lab_test(
    payload: LabTestCreate, db: Session = Depends(get_db), _=Depends(require_roles("doctor"))
):
    test = LabTestRequest(**payload.model_dump())
    db.add(test)
    db.flush()
    return LabTestOut(
        id=test.id, record_entry_id=test.record_entry_id, patient_id=test.patient_id, doctor_id=test.doctor_id,
        test_name=test.test_name, status=test.status, result=None, created_at=test.created_at,
    )


@router.patch("/lab-tests/{test_id}", response_model=LabTestOut)
def update_lab_result(
    test_id: str, payload: LabTestResultUpdate, db: Session = Depends(get_db),
    _=Depends(require_roles("doctor", "nurse")),
):
    test = db.query(LabTestRequest).filter(LabTestRequest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test not found")
    test.status = payload.status
    if payload.result:
        test.result_encrypted = encrypt_field(payload.result)
    return LabTestOut(
        id=test.id, record_entry_id=test.record_entry_id, patient_id=test.patient_id, doctor_id=test.doctor_id,
        test_name=test.test_name, status=test.status,
        result=decrypt_field(test.result_encrypted) if test.result_encrypted else None,
        created_at=test.created_at,
    )
