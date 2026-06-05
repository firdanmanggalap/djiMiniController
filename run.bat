@echo off
REM ============================================================
REM  DJI Mini -> Xbox Controller launcher
REM  Double-click this file to run. First run auto-sets-up the
REM  virtual environment + installs dependencies; later runs
REM  just launch the app. No need to "activate" anything.
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [setup] First run - creating virtual environment...
    python -m venv .venv || goto :error
    echo [setup] Installing dependencies...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)

echo [run] Starting DJI Mini -> Xbox Controller...
".venv\Scripts\python.exe" app.py
goto :end

:error
echo.
echo [ERROR] Setup failed. Make sure Python 3.10+ is installed and on PATH.

:end
echo.
pause
