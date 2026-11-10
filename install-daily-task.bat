@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\daily-task.ps1" -Action Install
set task_code=%errorlevel%
pause
exit /b %task_code%
