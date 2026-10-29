@echo off
setlocal
pushd "%~dp0..\.."
if errorlevel 1 (
  echo Cannot locate the AEGIS project root.
  pause
  exit /b 1
)
echo Starting AEGIS local-only development pilot...
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0Start-AegisPilot.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo.
  echo Local pilot setup did not complete. No cloud deployment was changed.
  echo Read docs\deployment\WINDOWS-HYBRID-PILOT.md for help.
)
popd
pause
exit /b %EXIT_CODE%
