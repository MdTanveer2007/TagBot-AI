@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
start "" http://localhost:5500
python backend\web_server.py
pause
