import uuid
from datetime import date, datetime

from sqlalchemy import JSON, CHAR, Date, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        Index("ix_patients_last_name", "last_name"),
        Index("ix_patients_dob", "date_of_birth"),
        Index("ix_patients_phone", "phone_number"),
        Index("ix_patients_deleted", "deleted_at"),
    )

    patient_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=new_uuid)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[str] = mapped_column(String(32), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(10), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    insurance_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    insurance_member_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(50), nullable=False, default="English")
    emergency_contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.utc_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.utc_timestamp(), onupdate=func.utc_timestamp()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CallLog(Base):
    __tablename__ = "call_logs"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=new_uuid)
    patient_id: Mapped[str | None] = mapped_column(CHAR(36), nullable=True, index=True)
    vapi_call_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    caller_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    collected_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, default="in_progress")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.utc_timestamp())
