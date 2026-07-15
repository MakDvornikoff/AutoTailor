@echo off
chcp 65001 > nul
echo ===================================================
echo   AutoTailor - Automatic Batch Processor
echo ===================================================
echo.
set PYTHONPATH=%~dp0src
python -m autotailor.cli --inbox
echo.
echo Press any key to exit...
pause > nul
