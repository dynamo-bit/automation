@echo off
echo Checking system requirements for Windows...

:: Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo  Python is not installed. Install it from: https://www.python.org/downloads/
    exit /b 1
)

:: Check for Multipass
where multipass >nul 2>nul
if %errorlevel% neq 0 (
    echo  Multipass is not installed. Install it from: https://multipass.run/
    exit /b 1
)

:: Create venv if missing
if not exist .venv (
    echo ⚙️ Creating virtual environment...
    python -m venv .venv
)

:: Activate venv (Windows)
call .venv\Scripts\activate.bat

:: Install dependencies
echo  Installing dependencies...
pip install fastapi uvicorn pydantic

:: Start API server
echo  Starting FastAPI server at http://localhost:8000
uvicorn apis.main:app --host 0.0.0.0 --port 8000
