@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" app.py
) else if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" app.py
) else (
    start "" pythonw app.py
)
exit
