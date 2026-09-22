@echo off
rem Command-line entry. For the GUI, double-click start_gui.bat instead.
cd /d "%~dp0"
python main.py %*
if errorlevel 1 pause
