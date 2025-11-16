@echo off
echo Setting up the environment...

python -m venv .venv

echo Entering environment
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo ✅ Setup complete!
pause

exit /b
