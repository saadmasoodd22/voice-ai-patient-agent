# Quiet voice test (live site already hosted)

The dashboard and API are on PythonAnywhere:

https://saadmasoodd22.pythonanywhere.com

Vapi tools should already use that URL. This laptop does not need to stay on for reviewers.

## Before a voice test at home

1. Confirm the dashboard opens: https://saadmasoodd22.pythonanywhere.com
2. Confirm health: https://saadmasoodd22.pythonanywhere.com/health
3. In PythonAnywhere **Web**, if the site is near expiry, click **Run until 1 month from today**.
4. In Vapi, Assistants → Cloud Care Patient Intake → **Talk**. Use fake names only.
5. After the call, refresh the dashboard and check **Patients** and **Call activity**.

Do not change the system prompt unless that quiet test shows a real problem.

## Local API (optional, DBeaver / MySQL)

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`. This is a separate MySQL database from the live SQLite file.
