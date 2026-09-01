from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Patient
from app.schemas import PatientCreate, PatientOut, PatientUpdate
from app.validators import (
    format_dob,
    format_phone,
    normalize_email,
    normalize_member_id,
    normalize_name,
    normalize_optional_text,
    normalize_phone,
    normalize_sex,
    normalize_state,
    normalize_zip,
    parse_dob,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_out(patient: Patient) -> PatientOut:
    return PatientOut(
        patient_id=patient.patient_id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=patient.date_of_birth,
        date_of_birth_display=format_dob(patient.date_of_birth),
        sex=patient.sex,
        phone_number=patient.phone_number,
        phone_display=format_phone(patient.phone_number) or patient.phone_number,
        email=patient.email,
        address_line_1=patient.address_line_1,
        address_line_2=patient.address_line_2,
        city=patient.city,
        state=patient.state,
        zip_code=patient.zip_code,
        insurance_provider=patient.insurance_provider,
        insurance_member_id=patient.insurance_member_id,
        preferred_language=patient.preferred_language,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_phone=patient.emergency_contact_phone,
        emergency_contact_phone_display=format_phone(patient.emergency_contact_phone),
        created_at=patient.created_at,
        updated_at=patient.updated_at,
        deleted_at=patient.deleted_at,
    )


def normalize_create(payload: PatientCreate) -> dict:
    language = normalize_optional_text(payload.preferred_language, "preferred_language", 50) or "English"
    address_line_1 = normalize_optional_text(payload.address_line_1, "address_line_1", 255)
    if not address_line_1:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="address_line_1 is required")
    city = normalize_optional_text(payload.city, "city", 100)
    if not city:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="city is required")

    return {
        "first_name": normalize_name(payload.first_name, "first_name"),
        "last_name": normalize_name(payload.last_name, "last_name"),
        "date_of_birth": parse_dob(payload.date_of_birth),
        "sex": normalize_sex(payload.sex),
        "phone_number": normalize_phone(payload.phone_number, required=True, field="phone_number"),
        "email": normalize_email(payload.email),
        "address_line_1": address_line_1,
        "address_line_2": normalize_optional_text(payload.address_line_2, "address_line_2", 255),
        "city": city,
        "state": normalize_state(payload.state),
        "zip_code": normalize_zip(payload.zip_code),
        "insurance_provider": normalize_optional_text(payload.insurance_provider, "insurance_provider", 255),
        "insurance_member_id": normalize_member_id(payload.insurance_member_id),
        "preferred_language": language,
        "emergency_contact_name": normalize_name(
            payload.emergency_contact_name, "emergency_contact_name", required=False
        ),
        "emergency_contact_phone": normalize_phone(
            payload.emergency_contact_phone, required=False, field="emergency_contact_phone"
        ),
    }


def find_active_by_phone(db: Session, phone: str) -> Patient | None:
    return (
        db.query(Patient)
        .filter(Patient.phone_number == phone, Patient.deleted_at.is_(None))
        .order_by(Patient.created_at.desc())
        .first()
    )


def list_patients(
    db: Session,
    last_name: str | None = None,
    date_of_birth: str | None = None,
    phone_number: str | None = None,
    include_deleted: bool = False,
) -> list[Patient]:
    query = db.query(Patient)
    if not include_deleted:
        query = query.filter(Patient.deleted_at.is_(None))
    if last_name:
        query = query.filter(Patient.last_name.ilike(last_name.strip()))
    if date_of_birth:
        query = query.filter(Patient.date_of_birth == parse_dob(date_of_birth))
    if phone_number:
        query = query.filter(
            Patient.phone_number == normalize_phone(phone_number, required=True, field="phone_number")
        )
    return query.order_by(Patient.created_at.desc()).all()


def get_patient(db: Session, patient_id: str, include_deleted: bool = True) -> Patient | None:
    query = db.query(Patient).filter(Patient.patient_id == patient_id)
    if not include_deleted:
        query = query.filter(Patient.deleted_at.is_(None))
    return query.first()


def create_patient(db: Session, payload: PatientCreate) -> Patient:
    data = normalize_create(payload)
    patient = Patient(**data)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient: Patient, payload: PatientUpdate) -> Patient:
    raw = payload.model_dump(exclude_unset=True)
    if "first_name" in raw:
        patient.first_name = normalize_name(raw["first_name"], "first_name")
    if "last_name" in raw:
        patient.last_name = normalize_name(raw["last_name"], "last_name")
    if "date_of_birth" in raw:
        patient.date_of_birth = parse_dob(raw["date_of_birth"])
    if "sex" in raw:
        patient.sex = normalize_sex(raw["sex"])
    if "phone_number" in raw:
        patient.phone_number = normalize_phone(raw["phone_number"], required=True, field="phone_number")
    if "email" in raw:
        patient.email = normalize_email(raw["email"])
    if "address_line_1" in raw:
        value = normalize_optional_text(raw["address_line_1"], "address_line_1", 255)
        if not value:
            from fastapi import HTTPException

            raise HTTPException(status_code=422, detail="address_line_1 is required")
        patient.address_line_1 = value
    if "address_line_2" in raw:
        patient.address_line_2 = normalize_optional_text(raw["address_line_2"], "address_line_2", 255)
    if "city" in raw:
        value = normalize_optional_text(raw["city"], "city", 100)
        if not value:
            from fastapi import HTTPException

            raise HTTPException(status_code=422, detail="city is required")
        patient.city = value
    if "state" in raw:
        patient.state = normalize_state(raw["state"])
    if "zip_code" in raw:
        patient.zip_code = normalize_zip(raw["zip_code"])
    if "insurance_provider" in raw:
        patient.insurance_provider = normalize_optional_text(raw["insurance_provider"], "insurance_provider", 255)
    if "insurance_member_id" in raw:
        patient.insurance_member_id = normalize_member_id(raw["insurance_member_id"])
    if "preferred_language" in raw:
        patient.preferred_language = (
            normalize_optional_text(raw["preferred_language"], "preferred_language", 50) or "English"
        )
    if "emergency_contact_name" in raw:
        patient.emergency_contact_name = normalize_name(
            raw["emergency_contact_name"], "emergency_contact_name", required=False
        )
    if "emergency_contact_phone" in raw:
        patient.emergency_contact_phone = normalize_phone(
            raw["emergency_contact_phone"], required=False, field="emergency_contact_phone"
        )
    patient.updated_at = utcnow()
    db.commit()
    db.refresh(patient)
    return patient


def soft_delete_patient(db: Session, patient: Patient) -> Patient:
    patient.deleted_at = utcnow()
    patient.updated_at = utcnow()
    db.commit()
    db.refresh(patient)
    return patient
