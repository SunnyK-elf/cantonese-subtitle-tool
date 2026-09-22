@echo off
echo Installing dependencies...
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo Install failed. Make sure Python 3.8+ is installed and in PATH.
    pause
    exit /b 1
)
echo.
echo Done! Now double-click start_gui.bat to launch the app.
pause
