@echo off
setlocal enabledelayedexpansion
echo Starting Guessify...

REM --- Launch backend in a new cmd window ---
start "" cmd /k "call .venv\Scripts\activate.bat & python app.py"

echo Waiting for backend to start on port 5000...

set "max_wait=30"
set "waited=0"

:WAIT_LOOP
REM Check every 1 second if port 5000 is listening
powershell -Command ^
  "$s=New-Object Net.Sockets.TcpClient; " ^
  "try { $s.Connect('127.0.0.1',5000) } catch {}; " ^
  "if ($s.Connected) { exit 0 } else { exit 1 }"
if %errorlevel%==0 goto BACKEND_READY

set /a waited+=1
if !waited! GEQ %max_wait% goto FAIL
timeout /t 1 >nul
goto WAIT_LOOP

:BACKEND_READY
echo  Backend is running! Launching browser...
start "" http://127.0.0.1:5000
goto END

:FAIL
echo  Backend did not start within %max_wait% seconds.
echo Check app.py for errors.
pause
goto END

:END
exit /b
