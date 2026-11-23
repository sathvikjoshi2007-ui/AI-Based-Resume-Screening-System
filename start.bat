@echo off
title AI Resume Screening System
color 0A
echo.
echo  ============================================================
echo   AI-Based Resume Screening System
echo   2nd Year CSE AI Project
echo  ============================================================
echo.
echo  [1/3] Checking Python installation...
python --version 2>nul || (
    echo  ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo.
echo  [2/3] Installing/checking dependencies...
python -m pip install -r requirements.txt -q
echo.
echo  [3/3] Starting Flask backend server...
echo.
echo  ============================================================
echo   Open your browser and go to:
echo   http://localhost:5000
echo  ============================================================
echo.
start "" http://localhost:5000
python backend\app.py
pause
