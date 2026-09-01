Set-Location "D:\Saad\Voice AI Agent"
Write-Host "Starting API on http://127.0.0.1:8000"
Write-Host "Leave this window open. In another window run: ngrok http 8000"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
