@echo off
chcp 65001 > nul
echo {"mode": "bw"} > "%~dp0config.json"
echo Output mode set to: BW (Black and White)
echo.
echo Press any key to exit...
pause > nul
