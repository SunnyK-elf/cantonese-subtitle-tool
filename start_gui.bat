@echo off
cd /d "%~dp0"
python gui.py
if errorlevel 1 (
    echo.
    echo Launch failed. Run install.bat first, and make sure Python is installed.
    pause
)
