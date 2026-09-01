from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.envelope import fail, ok, serialize
from app.schemas import PatientCreate, PatientUpdate
from app.services import (
    create_patient,
    get_patient,
    list_patients,
    soft_delete_patient,
    to_out,
    update_patient,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
def get_patients(
    last_name: str | None = Query(default=None),
    date_of_birth: str | None = Query(default=None),
    phone_number: str | None = Query(default=None),
    include_deleted: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    rows = list_patients(db, last_name, date_of_birth, phone_number, include_deleted)
    return ok([serialize(to_out(row)) for row in rows])


@router.get("/{patient_id}")
def get_patient_by_id(patient_id: str, db: Session = Depends(get_db)):
    patient = get_patient(db, patient_id)
    if not patient:
        return fail("Patient not found", 404, "not_found")
    return ok(serialize(to_out(patient)))


@router.post("")
def post_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = create_patient(db, payload)
    return ok(serialize(to_out(patient)), status_code=201)


@router.put("/{patient_id}")
def put_patient(patient_id: str, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = get_patient(db, patient_id)
    if not patient or patient.deleted_at is not None:
        return fail("Patient not found", 404, "not_found")
    updated = update_patient(db, patient, payload)
    return ok(serialize(to_out(updated)))


@router.delete("/{patient_id}")
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = get_patient(db, patient_id)
    if not patient:
        return fail("Patient not found", 404, "not_found")
    if patient.deleted_at is not None:
        return ok(serialize(to_out(patient)))
    deleted = soft_delete_patient(db, patient)
    return ok(serialize(to_out(deleted)))
