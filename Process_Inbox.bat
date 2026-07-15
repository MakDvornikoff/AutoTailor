@echo off
echo ===================================================
echo   AutoTailor - Automatic Batch Processor
echo ===================================================
echo.
python "%~dp0process_inbox.py"
echo.
echo Press any key to exit...
pause > nul
