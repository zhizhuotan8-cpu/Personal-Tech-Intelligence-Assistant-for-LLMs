@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set LITELLM_LOCAL_MODEL_COST_MAP=True
if not exist ".venv\Scripts\python.exe" (
  echo Python environment missing. Run: uv sync
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m trendradar --demo
set preview_code=%errorlevel%
pause
exit /b %preview_code%
