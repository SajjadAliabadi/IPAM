@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
:loop
python manage.py auto_scan
timeout /t 60 /nobreak
goto loop
