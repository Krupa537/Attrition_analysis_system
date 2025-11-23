@echo off
cd /d "%~dp0"
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment not found. Run run_backend.ps1 first to create it.
    pause
    exit /b 1
)

echo Starting uvicorn on 0.0.0.0:8000...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
