from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str | date
    sex: str
    phone_number: str
    email: str | None = None
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state: str
    zip_code: str
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str | None = "English"
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | date | None = None
    sex: str | None = None
    phone_number: str | None = None
    email: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    date_of_birth_display: str
    sex: str
    phone_number: str
    phone_display: str
    email: str | None
    address_line_1: str
    address_line_2: str | None
    city: str
    state: str
    zip_code: str
    insurance_provider: str | None
    insurance_member_id: str | None
    preferred_language: str
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    emergency_contact_phone_display: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class Envelope(BaseModel):
    data: Any = None
    error: dict | None = None


class PatientListQuery(BaseModel):
    last_name: str | None = None
    date_of_birth: str | None = None
    phone_number: str | None = None
    include_deleted: bool = False
