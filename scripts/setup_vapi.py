"""Create the Vapi assistant and attach it to the US number.

Creates a new assistant. To retarget the existing one:

    python scripts/update_vapi_assistant.py --server-url https://saadmasoodd22.pythonanywhere.com
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402

PROMPT = (ROOT / "prompts" / "system_prompt.md").read_text(encoding="utf-8")
API = "https://api.vapi.ai"


def patient_schema(required: bool = True) -> dict:
    props = {
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "date_of_birth": {"type": "string", "description": "MM/DD/YYYY"},
        "sex": {"type": "string", "enum": ["Male", "Female", "Other", "Decline to Answer"]},
        "phone_number": {"type": "string"},
        "email": {"type": "string"},
        "address_line_1": {"type": "string"},
        "address_line_2": {"type": "string"},
        "city": {"type": "string"},
        "state": {"type": "string"},
        "zip_code": {"type": "string"},
        "insurance_provider": {"type": "string"},
        "insurance_member_id": {"type": "string"},
        "preferred_language": {"type": "string"},
        "emergency_contact_name": {"type": "string"},
        "emergency_contact_phone": {"type": "string"},
    }
    req = [
        "first_name",
        "last_name",
        "date_of_birth",
        "sex",
        "phone_number",
        "address_line_1",
        "city",
        "state",
        "zip_code",
    ]
    return {"type": "object", "properties": props, "required": req if required else []}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", required=True, help="Public base URL, no trailing slash")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.vapi_api_key:
        raise SystemExit("VAPI_API_KEY missing")

    headers = {"Authorization": f"Bearer {settings.vapi_api_key}", "Content-Type": "application/json"}
    server = {
        "url": f"{args.server_url.rstrip('/')}/vapi/tools",
        "secret": settings.vapi_server_secret,
        "timeoutSeconds": 20,
    }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "lookup_patient",
                "description": "Find an existing patient by US phone number before creating a new record.",
                "parameters": {
                    "type": "object",
                    "properties": {"phone_number": {"type": "string"}},
                    "required": ["phone_number"],
                },
            },
            "server": server,
        },
        {
            "type": "function",
            "function": {
                "name": "create_patient",
                "description": "Save a confirmed new patient after read-back confirmation.",
                "parameters": patient_schema(True),
            },
            "server": server,
        },
        {
            "type": "function",
            "function": {
                "name": "update_patient",
                "description": "Update an existing patient when a duplicate phone is found and the caller wants changes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {"type": "string"},
                        **patient_schema(False)["properties"],
                    },
                    "required": ["patient_id"],
                },
            },
            "server": server,
        },
    ]

    assistant = {
        "name": "Cloud Care Patient Intake",
        "firstMessage": "Hi, you've reached Cloud Care Health patient registration. I'm Saad. I can get you set up in a few minutes. What is your first name?",
        "model": {
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.4,
            "messages": [{"role": "system", "content": PROMPT}],
            "tools": tools,
        },
        "voice": {"provider": "vapi", "voiceId": "Elliot"},
        "transcriber": {"provider": "deepgram", "model": "nova-2", "language": "en"},
        "endCallPhrases": ["goodbye", "that's all", "you're all set"],
        "serverUrl": f"{args.server_url.rstrip('/')}/vapi/end-call",
        "analysisPlan": {"summaryPrompt": "Summarize the patient registration call in 3 sentences."},
    }

    with httpx.Client(timeout=30) as client:
        created = client.post(f"{API}/assistant", headers=headers, json=assistant)
        created.raise_for_status()
        assistant_id = created.json()["id"]
        print("assistant_id", assistant_id)

        numbers = client.get(f"{API}/phone-number", headers=headers)
        numbers.raise_for_status()
        target = None
        for item in numbers.json():
            if str(item.get("number", "")).replace(" ", "").endswith("8604108127"):
                target = item
                break
        if not target and numbers.json():
            target = numbers.json()[0]
        if not target:
            raise SystemExit("No Vapi phone number found")

        patched = client.patch(
            f"{API}/phone-number/{target['id']}",
            headers=headers,
            json={"assistantId": assistant_id},
        )
        patched.raise_for_status()
        print("phone", target.get("number"), "id", target["id"])
        print(json.dumps({"assistant_id": assistant_id, "phone": target.get("number")}, indent=2))


if __name__ == "__main__":
    main()
