@echo off
echo Entering environment
call .venv\Scripts\activate.bat
echo Starting app.py
start "" python app.py
timeout /t 2 >nul
start http://127.0.0.1:5000
exit