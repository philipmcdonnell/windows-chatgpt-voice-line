@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\start_whisper_server.ps1"
if errorlevel 1 exit /b %errorlevel%
".\.venv\Scripts\python.exe" ".\voice_line.py"
