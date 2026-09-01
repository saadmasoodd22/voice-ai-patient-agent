# Voice AI Patient Registration
# Cloud Care Health — take-home assessment

Voice agent + REST API + MySQL + intake dashboard.

When a reviewer calls the US number, the agent collects patient demographics, confirms them, and saves through `POST /patients`. The portal reads the same MySQL database.

## Live demo

| Item | Value |
|---|---|
| Repository | https://github.com/saadmasoodd22/voice-ai-patient-agent |
| US phone number | `+1 (860) 410-8127` |
| API / dashboard | https://hastiness-rebate-doorpost.ngrok-free.dev (same URL). Local: `http://127.0.0.1:8000` |
| Test notes | Use **fake** demographics only. No HIPAA. No real patient data. Reviewers in the US can dial the number. I am in Pakistan and cannot place that US call myself. |

If the laptop or ngrok restarts, follow `docs/HOME_TEST.md` and re-run `scripts/setup_vapi.py` with the new ngrok URL. The assistant itself is not edited unless a quiet voice test shows a bug.

## Architecture

```
Caller
  -> Vapi (US number, STT, TTS, Groq LLM, tools)
      -> FastAPI /vapi/tools
          -> same patient service as REST
          -> MySQL 8 (`voice_ai`)
      -> /vapi/end-call stores transcript

Reviewer browser
  -> Dashboard
      -> GET /patients  GET /stats
```

Separation of concerns:

- **Telephony / voice** — Vapi. We did not build STT/TTS.
- **Conversation policy** — `prompts/system_prompt.md`
- **HTTP + validation** — FastAPI / Pydantic
- **Persistence** — MySQL `patients` + `call_logs`
- **Portal** — static HTML/CSS/JS served by FastAPI

The voice agent never writes SQL. It only calls tools that hit the API service layer.

## Tech stack (and why)

| Layer | Choice | Why |
|---|---|---|
| Voice | Vapi + free US number | Fastest path to a real inbound number; recommended by the brief |
| LLM | Groq (`llama-3.3-70b-versatile`) | Free API, low latency for voice |
| API | Python FastAPI | Clear validation, OpenAPI, quick to ship |
| DB | MySQL 8 Community (local) | Free, no cloud card, DBeaver-friendly, listed in the brief |
| Dashboard | Vanilla JS + Chart.js | No extra frontend host; charts read `/stats` |
| Tunnel | ngrok (free) | Makes localhost reachable for Vapi tool calls |

Oracle Cloud Always Free was considered; it requires a card for identity. Docker Oracle Free needs Windows virtualization/WSL, which this machine did not have. MySQL Community on Windows is the free path that actually runs.

## Patient model

Required: first name, last name, DOB, sex, phone, address line 1, city, state, ZIP.

Optional: email, address line 2, insurance, member id, language (default English), emergency contact.

Soft delete sets `deleted_at`. Rows are not hard-deleted. List endpoints hide them unless `include_deleted=true`.

## REST API

Envelope for every JSON response: `{ "data": ..., "error": null }`

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/patients` | Filters: `last_name`, `date_of_birth`, `phone_number` |
| GET | `/patients/{id}` | 404 if missing |
| POST | `/patients` | 201 + server-side validation |
| PUT | `/patients/{id}` | Partial updates |
| DELETE | `/patients/{id}` | Soft delete |
| GET | `/stats` | KPIs + chart series for the portal |
| POST | `/vapi/tools` | Voice tool dispatcher |
| POST | `/vapi/end-call` | Stores transcript |

Validation examples that return **422**: future DOB, 3-digit phone, invalid state, bad ZIP, non-alphabetic name.

## Local setup

1. Install Python 3.11+ and MySQL 8. Create database `voice_ai`.
2. Copy `.env.example` to `.env` and set `MYSQL_PASSWORD`, `GROQ_API_KEY`, `VAPI_API_KEY`.
3. Install and run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open `http://127.0.0.1:8000` — seed patients load on first boot so charts are not empty.
5. Tests: `pytest -q`

DBeaver: new connection `voice-ai-mysql` → `localhost:3306` / database `voice_ai` / user `root`. Enable `allowPublicKeyRetrieval=true` for MySQL 8. Do not reuse this connection against other databases.

## Public URL for Vapi

Vapi tools cannot call `localhost`. In a second terminal:

```bash
ngrok http 8000
```

Then:

```bash
python scripts/setup_vapi.py --server-url https://YOUR-NGROK-URL
```

Keep the API process and ngrok running while reviewers call.

## Environment variables

See `.env.example`. Never commit `.env`. Keys stay on the machine that runs the API.

## Known limitations / trade-offs

- The MySQL instance is local. The laptop (or a tunnel) must be on during review.
- Vapi free US numbers are inbound US-national. Outbound from that free number is limited.
- Groq + Vapi usage consumes Vapi credits (this account started with a small balance).
- Dashboard has no login. Fine for a time-boxed demo; not for real PHI.
- Not HIPAA compliant, by design.
- Appointment scheduling and a full Spanish voice path are only partially specified in the prompt, not separate products.

## What I would do next

- Move MySQL to a free hosted instance so the laptop can sleep.
- Add more Vapi credits before a live review window.
- Expand tests around Vapi tool payloads.
- Add webhook signature verification beyond the shared secret header.

## Demo data

First boot inserts ~28 fictional US patients so the portal graphs have shape. Add more from the dashboard (same `POST /patients`) or with SQL against `voice_ai` only.
