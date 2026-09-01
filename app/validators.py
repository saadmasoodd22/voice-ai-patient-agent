from __future__ import annotations

import re
from datetime import date, datetime

from fastapi import HTTPException

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

SEX_VALUES = {"Male", "Female", "Other", "Decline to Answer"}
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z\s\-']{0,49}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")
MEMBER_ID_RE = re.compile(r"^[A-Za-z0-9\-]{3,64}$")


def digits_only(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\D", "", value)


def normalize_phone(value: str | None, *, required: bool, field: str) -> str | None:
    digits = digits_only(value)
    if not digits:
        if required:
            raise HTTPException(status_code=422, detail=f"{field} is required and must be a valid US 10-digit number")
        return None
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise HTTPException(
            status_code=422,
            detail=f"{field} must be a valid US 10-digit phone number",
        )
    return digits


def normalize_name(value: str | None, field: str, *, required: bool = True) -> str | None:
    if value is None or not str(value).strip():
        if required:
            raise HTTPException(status_code=422, detail=f"{field} is required")
        return None
    cleaned = " ".join(str(value).strip().split())
    if not NAME_RE.match(cleaned) or not (1 <= len(cleaned) <= 50):
        raise HTTPException(
            status_code=422,
            detail=f"{field} must be 1–50 characters and contain only letters, spaces, hyphens, or apostrophes",
        )
    return cleaned


def parse_dob(value: str | date | None) -> date:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise HTTPException(status_code=422, detail="date_of_birth is required")
    if isinstance(value, date) and not isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        parsed = None
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
            try:
                parsed = datetime.strptime(text, fmt).date()
                break
            except ValueError:
                continue
        if parsed is None:
            raise HTTPException(status_code=422, detail="date_of_birth must be a valid date in MM/DD/YYYY")
    if parsed > date.today():
        raise HTTPException(status_code=422, detail="date_of_birth cannot be in the future")
    if parsed.year < 1900:
        raise HTTPException(status_code=422, detail="date_of_birth is not a realistic date")
    return parsed


def normalize_sex(value: str | None) -> str:
    if not value:
        raise HTTPException(status_code=422, detail="sex is required")
    mapping = {
        "m": "Male",
        "male": "Male",
        "f": "Female",
        "female": "Female",
        "other": "Other",
        "decline": "Decline to Answer",
        "decline to answer": "Decline to Answer",
        "prefer not to say": "Decline to Answer",
    }
    cleaned = str(value).strip()
    normalized = mapping.get(cleaned.lower(), cleaned)
    if normalized not in SEX_VALUES:
        raise HTTPException(
            status_code=422,
            detail="sex must be one of: Male, Female, Other, Decline to Answer",
        )
    return normalized


def normalize_state(value: str | None) -> str:
    if not value:
        raise HTTPException(status_code=422, detail="state is required")
    state = str(value).strip().upper()
    if state not in US_STATES:
        raise HTTPException(status_code=422, detail="state must be a valid 2-letter US state abbreviation")
    return state


def normalize_zip(value: str | None) -> str:
    if not value:
        raise HTTPException(status_code=422, detail="zip_code is required")
    zip_code = str(value).strip()
    if not ZIP_RE.match(zip_code):
        raise HTTPException(status_code=422, detail="zip_code must be 5-digit or ZIP+4 US format")
    return zip_code


def normalize_email(value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    email = str(value).strip()
    if not EMAIL_RE.match(email) or len(email) > 255:
        raise HTTPException(status_code=422, detail="email must be a valid email address")
    return email


def normalize_optional_text(value: str | None, field: str, max_len: int) -> str | None:
    if value is None or not str(value).strip():
        return None
    cleaned = " ".join(str(value).strip().split())
    if len(cleaned) > max_len:
        raise HTTPException(status_code=422, detail=f"{field} must be at most {max_len} characters")
    return cleaned


def normalize_member_id(value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    member_id = str(value).strip()
    if not MEMBER_ID_RE.match(member_id):
        raise HTTPException(status_code=422, detail="insurance_member_id must be alphanumeric")
    return member_id


def format_dob(value: date) -> str:
    return value.strftime("%m/%d/%Y")


def format_phone(value: str | None) -> str | None:
    if not value:
        return None
    return f"({value[0:3]}) {value[3:6]}-{value[6:10]}"
