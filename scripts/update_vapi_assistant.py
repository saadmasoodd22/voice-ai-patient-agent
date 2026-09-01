"""Patch the live Vapi assistant with the current prompt and branding."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402

PROMPT = (ROOT / "prompts" / "system_prompt.md").read_text(encoding="utf-8")
API = "https://api.vapi.ai"
FIRST_MESSAGE = (
    "Hi, you've reached Cloud Care Health patient registration. "
    "I'm Saad. I can get you set up in a few minutes. What is your first name?"
)


def main() -> None:
    settings = get_settings()
    assistant_id = settings.vapi_assistant_id
    if not assistant_id:
        raise SystemExit("VAPI_ASSISTANT_ID missing")
    headers = {
        "Authorization": f"Bearer {settings.vapi_api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=30) as client:
        current = client.get(f"{API}/assistant/{assistant_id}", headers=headers)
        current.raise_for_status()
        body = current.json()
        model = body.get("model") or {}
        messages = model.get("messages") or [{"role": "system", "content": PROMPT}]
        if messages:
            messages[0]["content"] = PROMPT
        else:
            messages = [{"role": "system", "content": PROMPT}]
        model["messages"] = messages
        patch = {
            "name": "Cloud Care Patient Intake",
            "firstMessage": FIRST_MESSAGE,
            "model": model,
            "voice": {"provider": "vapi", "voiceId": "Elliot"},
        }
        updated = client.patch(f"{API}/assistant/{assistant_id}", headers=headers, json=patch)
        updated.raise_for_status()
        print("updated", assistant_id, updated.json().get("name"))


if __name__ == "__main__":
    main()
