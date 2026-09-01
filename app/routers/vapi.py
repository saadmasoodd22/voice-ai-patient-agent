import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.envelope import fail, ok, serialize
from app.models import CallLog
from app.schemas import PatientCreate, PatientUpdate
from app.services import (
    create_patient,
    find_active_by_phone,
    get_patient,
    to_out,
    update_patient,
)
from app.validators import normalize_phone

logger = logging.getLogger("voice-agent")
router = APIRouter(prefix="/vapi", tags=["vapi"])
settings = get_settings()


def _authorize(secret: str | None) -> bool:
    expected = settings.vapi_server_secret
    if not expected:
        return True
    return secret == expected


def _tool_result(tool_call_id: str, payload: dict) -> dict:
    return {"toolCallId": tool_call_id, "result": json.dumps(payload)}


def lookup_by_phone(db: Session, phone: str) -> dict:
    normalized = normalize_phone(phone, required=True, field="phone_number")
    patient = find_active_by_phone(db, normalized)
    if not patient:
        return {"found": False, "phone_number": normalized}
    body = serialize(to_out(patient))
    return {"found": True, "patient": body}


def create_or_advise(db: Session, arguments: dict) -> dict:
    phone = normalize_phone(arguments.get("phone_number"), required=True, field="phone_number")
    existing = find_active_by_phone(db, phone)
    if existing:
        return {
            "created": False,
            "duplicate": True,
            "message": (
                f"It looks like we already have a record for {existing.first_name} {existing.last_name}. "
                "Ask if they want to update that record instead of creating a new one."
            ),
            "patient": serialize(to_out(existing)),
        }
    patient = create_patient(db, PatientCreate(**arguments))
    logger.info("VOICE_SAVE_SUCCESS %s", json.dumps(serialize(to_out(patient))))
    return {
        "created": True,
        "duplicate": False,
        "message": f"You're all set, {patient.first_name}. Registration saved.",
        "patient": serialize(to_out(patient)),
    }


def apply_update(db: Session, arguments: dict) -> dict:
    patient_id = arguments.get("patient_id")
    if not patient_id:
        return {"updated": False, "message": "patient_id is required to update a record"}
    patient = get_patient(db, patient_id)
    if not patient or patient.deleted_at is not None:
        return {"updated": False, "message": "No active patient found for that id"}
    update_fields = {k: v for k, v in arguments.items() if k != "patient_id" and v not in (None, "")}
    updated = update_patient(db, patient, PatientUpdate(**update_fields))
    logger.info("VOICE_UPDATE_SUCCESS %s", json.dumps(serialize(to_out(updated))))
    return {
        "updated": True,
        "message": f"Thanks {updated.first_name}, your information has been updated.",
        "patient": serialize(to_out(updated)),
    }


def dispatch(name: str, arguments: dict, db: Session) -> dict:
    if name in {"lookup_patient", "lookupPatient", "get_patient_by_phone"}:
        phone = arguments.get("phone_number") or arguments.get("phone")
        return lookup_by_phone(db, phone)
    if name in {"create_patient", "createPatient", "save_patient"}:
        return create_or_advise(db, arguments)
    if name in {"update_patient", "updatePatient"}:
        return apply_update(db, arguments)
    return {"ok": False, "message": f"Unknown tool {name}"}


@router.post("/tools")
async def vapi_tools(
    request: Request,
    db: Session = Depends(get_db),
    x_vapi_secret: str | None = Header(default=None, alias="X-Vapi-Secret"),
):
    if not _authorize(x_vapi_secret):
        return fail("Unauthorized tool request", 401, "unauthorized")

    body: dict[str, Any] = await request.json()
    logger.info("VAPI_TOOL_REQUEST %s", json.dumps(body)[:4000])
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
            logger.exception("VAPI_TOOL_FAILED")
            payload = {"ok": False, "message": "I could not save that just now. Please try again."}
            payload["error"] = str(exc)
        results.append(_tool_result(tool_id, payload))

    if not results and body.get("phone_number"):
        payload = lookup_by_phone(db, body["phone_number"])
        return ok(payload)

    return {"results": results}


@router.post("/end-call")
async def vapi_end_call(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
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
    logger.info("CALL_TRANSCRIPT_SAVED call_id=%s", call.get("id"))
    return ok({"stored": True})
