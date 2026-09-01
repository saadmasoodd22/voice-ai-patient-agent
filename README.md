# Cloud Care Health — Voice AI Patient Registration

Voice agent + REST API + dashboard for the take-home assessment.

When a reviewer calls the US number, the agent collects demographics, confirms them, and saves through the same service as `POST /patients`. The dashboard reads that same database.

## Live demo

| Item | Value |
|---|---|
| Repository | https://github.com/saadmasoodd22/voice-ai-patient-agent |
| US phone | `+1 (860) 410-8127` |
| API / dashboard | https://saadmasoodd22.pythonanywhere.com |

Use **fake** demographics only. Not HIPAA. I am in Pakistan and cannot dial this US number myself. Current dashboard rows are dummy seed data. A US-to-US call, or **Add patient** on the portal, writes a row you can see on the dashboard.

## Architecture

```
Caller → Vapi (STT/TTS + Groq LLM + tools)
      → /vapi/tools → patient service → SQLite (live) / MySQL (local)
      → /vapi/end-call stores transcript

Browser → dashboard → GET /patients  GET /stats
```

- Voice: Vapi (we did not build STT/TTS)
- Conversation policy: `prompts/system_prompt.md`
- Validation + REST: FastAPI locally; sync WSGI on PythonAnywhere
- Voice never writes SQL. Tools call the service layer.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Voice | Vapi + US number | Fastest path to a real inbound line |
| LLM | Groq `llama-3.3-70b-versatile` | Free, low latency |
| Live API | Python WSGI on PythonAnywhere | Stays up without this laptop |
| Live DB | SQLite | Allowed by the brief; free PA has no MySQL |
| Local DB | MySQL 8 `voice_ai` | DBeaver on this machine only |
| Dashboard | HTML + Chart.js | Bonus UI on the same host |

## REST API

Every JSON body: `{ "data": ..., "error": null }`

| Method | Path |
|---|---|
| GET | `/health` |
| GET | `/patients` (`last_name`, `date_of_birth`, `phone_number`) |
| GET | `/patients/{id}` |
| POST | `/patients` |
| PUT | `/patients/{id}` |
| DELETE | `/patients/{id}` (soft delete) |
| GET | `/stats` |
| POST | `/vapi/tools` |
| POST | `/vapi/end-call` |

422 on invalid DOB, phone, state, ZIP, or name.

## Local setup

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest -q
```

Open `http://127.0.0.1:8000`. Keys stay in `.env` (not in git).

## Limitations

- PythonAnywhere free sites need **Run until 1 month from today** when they expire.
- Live SQLite and local MySQL are separate copies.
- Free Vapi US numbers are inbound US-national.
- Dashboard has no login. Demo only. Not HIPAA.
- Appointment scheduling was skipped. Spanish can be requested in the prompt; it is not a separate product.

## Next

- Renew the PythonAnywhere app before review if needed.
- Add Vapi credits if the balance is low.
- More tests around Vapi tool payloads.
