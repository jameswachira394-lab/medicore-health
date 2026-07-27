from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from shared_common.security import make_current_user_dependency, make_require_roles

from app.core.config import settings
from app.core.db import get_db
from app.models.doctor import Doctor, DoctorAvailability
from app.schemas.doctor import AvailabilityCreate, AvailabilityOut, DoctorCreate, DoctorOut

router = APIRouter(prefix="/doctors", tags=["doctors"])
get_current_user = make_current_user_dependency(settings.JWT_SECRET, settings.JWT_ALGORITHM)
require_roles = make_require_roles(get_current_user)


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def add_doctor(
    payload: DoctorCreate, db: Session = Depends(get_db),
    _=Depends(require_roles("hospital_admin", "system_admin")),
):
    if db.query(Doctor).filter(Doctor.license_number == payload.license_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="License number already registered")
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.flush()
    return doctor


@router.get("/me", response_model=DoctorOut)
def get_my_doctor_profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Lets a doctor discover their own doctor.id without a directory search."""
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.sub).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No doctor profile linked to this account")
    return doctor


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor


@router.get("", response_model=list[DoctorOut])
def search_doctors(
    specialization: str | None = None, department: str | None = None,
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    """Open to any authenticated role — patients need this to find specialists."""
    query = db.query(Doctor)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    if department:
        query = query.filter(Doctor.department.ilike(f"%{department}%"))
    return query.limit(50).all()


@router.post("/{doctor_id}/availability", response_model=AvailabilityOut, status_code=status.HTTP_201_CREATED)
def set_availability(
    doctor_id: str, payload: AvailabilityCreate, db: Session = Depends(get_db),
    current_user=Depends(require_roles("doctor", "hospital_admin", "system_admin")),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    if current_user.role == "doctor" and current_user.sub != doctor.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot set another doctor's availability")

    block = DoctorAvailability(doctor_id=doctor_id, **payload.model_dump())
    db.add(block)
    db.flush()
    return block


@router.get("/{doctor_id}/availability", response_model=list[AvailabilityOut])
def list_availability(doctor_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(DoctorAvailability).filter(DoctorAvailability.doctor_id == doctor_id).all()
