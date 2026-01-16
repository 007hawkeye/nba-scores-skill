@echo off
setlocal enabledelayedexpansion

echo ========================================
echo     NBA Real-time Scores Launcher
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)
echo Python found
echo.

echo Checking dependencies...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing requests...
    pip install requests
)

python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installing PyQt5...
    pip install PyQt5
)

python -c "import dateutil" >nul 2>&1
if errorlevel 1 (
    echo Installing python-dateutil...
    pip install python-dateutil
)

echo Dependencies OK
echo.

echo Starting NBA Scores Panel...
echo.
cd scripts
start python nba_scores_panel.py

echo.
echo NBA Scores Panel started successfully!
echo Check your desktop for the panel window
echo.
pause
