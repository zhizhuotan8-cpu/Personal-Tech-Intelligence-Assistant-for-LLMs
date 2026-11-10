@echo off
if exist "%~dp0output\preview\latest-success.html" (
  start "" "%~dp0output\preview\latest-success.html"
) else (
  echo No successful report yet. Run start-preview.bat first.
  pause
)
