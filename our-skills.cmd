@echo off
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 "%~dp0scripts\our_skills.py" %*
) else (
  python "%~dp0scripts\our_skills.py" %*
)
