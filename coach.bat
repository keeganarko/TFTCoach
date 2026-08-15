@echo off
rem TFT Coach launcher (Windows). Usage: coach.bat [refresh|--check|--primary]
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo venv missing — run setup_windows.bat first
  exit /b 1
)
.venv\Scripts\python.exe run_coach.py %*
