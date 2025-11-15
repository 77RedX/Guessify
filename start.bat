@echo off
echo Starting Guessify...

REM --- Launch backend in a NEW cmd window (not VS Code terminal) ---
start "" cmd /k "call .venv\Scripts\activate.bat & python app.py"

REM --- Small delay to allow backend to boot ---
timeout /t 2 >nul

REM --- Open browser ---
start "" http://127.0.0.1:5000

exit /b
