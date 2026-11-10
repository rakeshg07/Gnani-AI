



# VoiceIQ India - Client PowerShell Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting VoiceIQ India Frontend Client" -ForegroundColor Green
Write-Host "Local URL: http://localhost:5000" -ForegroundColor Yellow
Write-Host "Proxying /api to http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

Set-Location "$PSScriptRoot\client"

npm run dev
