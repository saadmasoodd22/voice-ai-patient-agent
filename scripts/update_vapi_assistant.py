"""Patch the live Vapi assistant with the current prompt, branding, and server URL."""

from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server-url",
        default="https://saadmasoodd22.pythonanywhere.com",
        help="Public API base URL, no trailing slash",
    )
    args = parser.parse_args()
    settings = get_settings()
    assistant_id = settings.vapi_assistant_id
    if not assistant_id:
        raise SystemExit("VAPI_ASSISTANT_ID missing")
    headers = {
        "Authorization": f"Bearer {settings.vapi_api_key}",
        "Content-Type": "application/json",
    }
    base = args.server_url.rstrip("/")
    server = {
        "url": f"{base}/vapi/tools",
        "secret": settings.vapi_server_secret,
        "timeoutSeconds": 20,
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
        for tool in model.get("tools") or []:
            if isinstance(tool, dict) and tool.get("type") == "function":
                tool["server"] = server
        patch = {
            "name": "Cloud Care Patient Intake",
            "firstMessage": FIRST_MESSAGE,
            "model": model,
            "voice": {"provider": "vapi", "voiceId": "Elliot"},
            "serverUrl": f"{base}/vapi/end-call",
        }
        updated = client.patch(f"{API}/assistant/{assistant_id}", headers=headers, json=patch)
        updated.raise_for_status()
        print("updated", assistant_id, updated.json().get("name"), "server", base)


if __name__ == "__main__":
    main()
