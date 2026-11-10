@echo off
title VoiceIQ India — Backend (Port 8000)
echo ===================================================
echo Starting VoiceIQ India FastAPI Backend Server
echo API Base: http://127.0.0.1:8000
echo Swagger Docs: http://127.0.0.1:8000/docs
echo ===================================================
cd /d "%~dp0backend"

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
