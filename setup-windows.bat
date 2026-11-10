@echo off
cd /d "%~dp0"
uv sync --frozen
if errorlevel 1 (
  pause
  exit /b 1
)
echo Ready. Run start-preview.bat or install-daily-task.bat.
pause
