@echo off
echo ==========================================================
echo    DUKAANPULSE -- LAUNCHING LOCAL MERCHANT RESEARCH AGENT
echo ==========================================================

if not exist ".venv" (
    echo Creating virtual environment .venv...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

if not exist ".env" (
    echo Creating default .env from .env.example...
    copy .env.example .env
)

echo.
echo Running system pre-flight smoke tests...
python smoke_test.py

echo.
echo Starting DukaanPulse on http://127.0.0.1:8000 ...
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
