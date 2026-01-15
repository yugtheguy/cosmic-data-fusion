#!/bin/bash
# Quick start for verification script

echo "🪐 Planet Hunter Live Verification"
echo "===================================="
echo ""
echo "Step 1: Install dependencies (if not already installed)"
pip install lightkurve matplotlib requests
echo ""

echo "Step 2: Start the backend server (in a separate terminal if not already running)"
echo "  Command: uvicorn app.main:app --reload"
echo ""

echo "Step 3: Run this verification script"
python tests/verify_planet_hunter_live.py
