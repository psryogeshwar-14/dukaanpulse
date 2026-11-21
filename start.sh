#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "   DUKAANPULSE — LAUNCHING LOCAL MERCHANT RESEARCH AGENT   "
echo "=========================================================="

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment .venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

if [ ! -f ".env" ]; then
    echo "Creating default .env from .env.example..."
    cp .env.example .env
fi

echo ""
echo "Running system pre-flight smoke tests..."
python smoke_test.py

echo ""
echo "Starting DukaanPulse on http://127.0.0.1:8000 ..."
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
