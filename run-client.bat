@echo off
title VoiceIQ India — Client (Port 5000)
echo ===================================================
echo Starting VoiceIQ India Frontend Client
echo Local URL: http://localhost:5000
echo Proxying /api to http://127.0.0.1:8000
echo ===================================================
cd /d "%~dp0client"

npm run dev
pause
