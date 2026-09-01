# Restart at home (voice agent unchanged)

The intake prompt and Vapi tools are frozen until you do a quiet voice test.

If this laptop is shut down, ngrok dies and Vapi cannot reach MySQL. Do this after you are home:

1. Open Docker is NOT required. MySQL Windows service should start by itself.
2. Open PowerShell in `D:\Saad\Voice AI Agent`
3. Start the API:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. In a second PowerShell:

```powershell
ngrok http 8000
```

5. Copy the new `https://....ngrok-free.dev` URL from ngrok (it changes every restart).
6. In a third PowerShell:

```powershell
python scripts/setup_vapi.py --server-url https://YOUR-NEW-NGROK-URL
```

7. Test with **Talk** in the Vapi dashboard (Assistants → Cloud Care Patient Intake → Talk), using fake names only.
8. Confirm the new patient on `http://127.0.0.1:8000` or the ngrok URL.

Do not change the system prompt unless the quiet test shows a real problem.
