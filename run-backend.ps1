# VoiceIQ India - Backend PowerShell Launcher

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting VoiceIQ India FastAPI Backend Server" -ForegroundColor Green
Write-Host "API Base: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

Set-Location "$PSScriptRoot\backend"

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
