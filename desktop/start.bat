@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Could not find the app's virtual environment ^(.venv^).
    echo Run this once first, from a command prompt in this folder:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
