@echo off
rem One-time TFT Coach setup on Windows. Run from the repo folder.
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Install Python 3.12+ from python.org first ^(check "tcl/tk" and "py launcher" in the installer^)
  exit /b 1
)
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip install mss pillow numpy pytesseract
echo.
echo ---- Remaining steps ----
echo 1. Tesseract OCR:   winget install UB-Mannheim.TesseractOCR
echo    ^(tick "add to PATH" in its installer, or add it yourself^)
echo 2. Claude Code:     npm install -g @anthropic-ai/claude-code
echo    then run:        claude     ^(log in once with your Max account^)
echo 3. Pull live data:  coach.bat refresh
echo 4. In a TFT planning phase, auto-calibrate:
echo       .venv\Scripts\python.exe -m tftcoach.calibrate --auto
echo 5. Play:            coach.bat
