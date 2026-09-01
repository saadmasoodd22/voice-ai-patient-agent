"""WSGI app for PythonAnywhere (sync). Local dev still uses uvicorn app.main:app."""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import traceback
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs
from uuid import UUID

PROJECT = Path("/home/saadmasoodd22/voice-ai-patient-agent")
if not PROJECT.is_dir():
    PROJECT = Path(__file__).resolve().parent

os.chdir(PROJECT)
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

if Path("/home/saadmasoodd22").is_dir():
    os.environ["APP_ENV"] = "pythonanywhere"
    os.environ["SKIP_LIFESPAN"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:////home/saadmasoodd22/voice-ai-patient-agent/voice_ai.db"
    os.environ["PUBLIC_BASE_URL"] = "https://saadmasoodd22.pythonanywhere.com"

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import case, func

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.envelope import serialize
from app.models import CallLog, Patient
from app.routers.vapi import _authorize, _tool_result, dispatch, lookup_by_phone
from app.schemas import PatientCreate, PatientUpdate
from app.seed import seed_patients
from app.services import (
    create_patient,
    get_patient,
    list_patients,
    soft_delete_patient,
    to_out,
    update_patient,
)

FRONTEND = PROJECT / "frontend"
settings = get_settings()

Base.metadata.create_all(bind=engine)
_seed_db = SessionLocal()
try:
    seed_patients(_seed_db)
finally:
    _seed_db.close()


def collect_stats(db) -> dict:
    active = db.query(Patient).filter(Patient.deleted_at.is_(None))
    total = active.count()
    with_insurance = active.filter(Patient.insurance_provider.isnot(None)).count()
    with_emergency = active.filter(Patient.emergency_contact_name.isnot(None)).count()
    week_ago = date.today() - timedelta(days=7)
    new_this_week = active.filter(func.date(Patient.created_at) >= week_ago).count()

    def grouped(column):
        rows = (
            db.query(column, func.count(Patient.patient_id))
            .filter(Patient.deleted_at.is_(None))
            .group_by(column)
            .order_by(func.count(Patient.patient_id).desc())
            .all()
        )
        return [{"label": value or "Unknown", "value": count} for value, count in rows]

    start = date.today() - timedelta(days=29)
    day_rows = (
        db.query(func.date(Patient.created_at), func.count(Patient.patient_id))
        .filter(Patient.deleted_at.is_(None), func.date(Patient.created_at) >= start)
        .group_by(func.date(Patient.created_at))
        .all()
    )
    counts_by_day = {str(day): count for day, count in day_rows}
    registrations = []
    for offset in range(30):
        day = start + timedelta(days=offset)
        registrations.append({"label": day.isoformat(), "value": counts_by_day.get(str(day), 0)})

    recent_calls = db.query(CallLog).order_by(CallLog.created_at.desc()).limit(10).all()
    return {
        "kpis": {
            "total_patients": total,
            "new_this_week": new_this_week,
            "with_insurance": with_insurance,
            "with_emergency_contact": with_emergency,
            "recent_calls": db.query(func.count(CallLog.id)).scalar() or 0,
        },
        "by_state": grouped(Patient.state),
        "by_sex": grouped(Patient.sex),
        "by_language": grouped(Patient.preferred_language),
        "by_insurance": grouped(
            case((Patient.insurance_provider.is_(None), "Uninsured / not provided"), else_=Patient.insurance_provider)
        ),
        "registrations": registrations,
        "recent_calls": [
            {
                "id": row.id,
                "patient_id": row.patient_id,
                "caller_number": row.caller_number,
                "outcome": row.outcome,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in recent_calls
        ],
    }


def _json_bytes(payload: dict, status: str) -> tuple[str, list[tuple[str, str]], bytes]:
    body = json.dumps(payload).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]
    return status, headers, body


def _ok(data, status: str = "200 OK") -> tuple[str, list[tuple[str, str]], bytes]:
    return _json_bytes({"data": data, "error": None}, status)


def _fail(message: str, status: str, code: str | None = None) -> tuple[str, list[tuple[str, str]], bytes]:
    status_code = status.split(" ", 1)[0]
    return _json_bytes(
        {"data": None, "error": {"message": message, "code": code or status_code}},
        status,
    )


def _read_json(environ) -> dict:
    length = int(environ.get("CONTENT_LENGTH") or 0)
    raw = environ["wsgi.input"].read(length) if length else b""
    if not raw:
        return {}
    parsed = json.loads(raw.decode("utf-8"))
    return parsed if isinstance(parsed, dict) else {}


def _qs(environ) -> dict[str, str]:
    pairs = parse_qs(environ.get("QUERY_STRING") or "", keep_blank_values=False)
    return {key: values[-1] for key, values in pairs.items() if values}


def _header(environ, name: str) -> str | None:
    key = "HTTP_" + name.upper().replace("-", "_")
    return environ.get(key)


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def _file(path: Path, content_type: str) -> tuple[str, list[tuple[str, str]], bytes]:
    if not path.is_file():
        return _fail("Not found", "404 Not Found", "not_found")
    body = path.read_bytes()
    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
    ]
    return "200 OK", headers, body


def _handle(environ) -> tuple[str, list[tuple[str, str]], bytes]:
    method = (environ.get("REQUEST_METHOD") or "GET").upper()
    path = environ.get("PATH_INFO") or "/"
    if len(path) > 1:
        path = path.rstrip("/")

    if method == "GET" and path == "/health":
        return _ok({"status": "ok", "service": settings.app_name, "host": "wsgi"})

    if method == "GET" and path == "/meta":
        return _ok(
            {
                "service": settings.app_name,
                "phone_number": settings.vapi_phone_number or "+18604108127",
                "public_base_url": settings.public_base_url,
                "dashboard": "/",
                "api_docs": "/docs",
            }
        )

    if method == "GET" and path in {"", "/"}:
        return _file(FRONTEND / "index.html", "text/html; charset=utf-8")

    if method == "GET" and path.startswith("/static/"):
        name = path[len("/static/") :]
        target = (FRONTEND / name).resolve()
        if FRONTEND.resolve() not in target.parents and target != FRONTEND.resolve():
            return _fail("Not found", "404 Not Found", "not_found")
        guessed, _ = mimetypes.guess_type(str(target))
        return _file(target, guessed or "application/octet-stream")

    db = SessionLocal()
    try:
        if method == "GET" and path == "/stats":
            return _ok(collect_stats(db))

        if method == "GET" and path == "/patients":
            query = _qs(environ)
            rows = list_patients(
                db,
                last_name=query.get("last_name"),
                date_of_birth=query.get("date_of_birth"),
                phone_number=query.get("phone_number"),
                include_deleted=query.get("include_deleted", "").lower() in {"1", "true", "yes"},
            )
            return _ok([serialize(to_out(row)) for row in rows])

        if method == "POST" and path == "/patients":
            patient = create_patient(db, PatientCreate.model_validate(_read_json(environ)))
            return _ok(serialize(to_out(patient)), "201 Created")

        if path.startswith("/patients/"):
            patient_id = path.split("/", 2)[-1]
            if not _is_uuid(patient_id):
                return _fail("Patient not found", "404 Not Found", "not_found")
            patient = get_patient(db, patient_id)
            if method == "GET":
                if not patient:
                    return _fail("Patient not found", "404 Not Found", "not_found")
                return _ok(serialize(to_out(patient)))
            if method == "PUT":
                if not patient or patient.deleted_at is not None:
                    return _fail("Patient not found", "404 Not Found", "not_found")
                updated = update_patient(db, patient, PatientUpdate.model_validate(_read_json(environ)))
                return _ok(serialize(to_out(updated)))
            if method == "DELETE":
                if not patient:
                    return _fail("Patient not found", "404 Not Found", "not_found")
                if patient.deleted_at is not None:
                    return _ok(serialize(to_out(patient)))
                deleted = soft_delete_patient(db, patient)
                return _ok(serialize(to_out(deleted)))

        if method == "POST" and path == "/vapi/tools":
            if not _authorize(_header(environ, "X-Vapi-Secret")):
                return _fail("Unauthorized tool request", "401 Unauthorized", "unauthorized")
            body = _read_json(environ)
            message = body.get("message") or body
            tool_calls = (
                message.get("toolCallList")
                or message.get("toolCalls")
                or body.get("toolCallList")
                or []
            )
            results = []
            for call in tool_calls:
                function = call.get("function") or {}
                name = function.get("name") or call.get("name")
                raw_args = function.get("arguments") or call.get("arguments") or {}
                if isinstance(raw_args, str):
                    raw_args = json.loads(raw_args or "{}")
                tool_id = call.get("id") or call.get("toolCallId") or "tool"
                try:
                    payload = dispatch(name, raw_args, db)
                except Exception as exc:  # noqa: BLE001
                    payload = {
                        "ok": False,
                        "message": "I could not save that just now. Please try again.",
                        "error": str(exc),
                    }
                results.append(_tool_result(tool_id, payload))
            if not results and body.get("phone_number"):
                return _ok(lookup_by_phone(db, body["phone_number"]))
            return _json_bytes({"results": results}, "200 OK")

        if method == "POST" and path == "/vapi/end-call":
            body = _read_json(environ)
            message = body.get("message") or body
            call = message.get("call") or {}
            artifact = message.get("artifact") or {}
            transcript = artifact.get("transcript") or message.get("transcript")
            log = CallLog(
                vapi_call_id=call.get("id"),
                caller_number=(call.get("customer") or {}).get("number"),
                transcript=transcript if isinstance(transcript, str) else json.dumps(transcript) if transcript else None,
                collected_payload=body,
                outcome=message.get("endedReason") or "completed",
            )
            db.add(log)
            db.commit()
            return _ok({"stored": True})

        if method == "GET" and path == "/docs":
            return _ok({"message": "OpenAPI UI is local-only. Use /health, /patients, and /stats on this host."})

        return _fail("Not found", "404 Not Found", "not_found")
    finally:
        db.close()


def application(environ, start_response):
    try:
        status, headers, body = _handle(environ)
    except HTTPException as exc:
        detail = exc.detail
        if isinstance(detail, list):
            detail = "; ".join(str(item) for item in detail)
        status, headers, body = _fail(str(detail), f"{exc.status_code} Error")
    except ValidationError as exc:
        messages = []
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", []) if part != "body")
            messages.append(f"{loc}: {err.get('msg')}" if loc else str(err.get("msg")))
        status, headers, body = _fail("; ".join(messages) or "Invalid request", "422 Unprocessable Entity", "validation_error")
    except Exception:
        status, headers, body = (
            "500 Internal Server Error",
            [("Content-Type", "text/plain; charset=utf-8")],
            traceback.format_exc().encode("utf-8"),
        )
    start_response(status, headers)
    return [body]
