@echo off
title CYBER-FORENSICS PRO V5.0
color 0a

echo =========================================================================
echo       CYBER-FORENSICS PRO V5.0 (ENTERPRISE EDITION) INITIALIZATION
echo =========================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH environment variable.
    echo Please download and install Python from https://www.python.org/downloads/
    pause
    exit /b
)

echo [INFO] Launching CYBER-FORENSICS PRO V5.0 GUI...
echo.

:: Launch the main application directly
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Encountered missing dependencies. Auto-installing...
    pip install opencv-python ultralytics customtkinter pillow requests mediapipe playwright
    python -m playwright install chromium >nul 2>&1
    echo.
    echo [INFO] Retrying application launch...
    python main.py
)

echo.
echo [INFO] Application session closed cleanly.
pause
