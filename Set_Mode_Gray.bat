@echo off
chcp 65001 > nul
echo {"mode": "gray"} > "%~dp0config.json"
echo Output mode set to: GRAY (Clean Grayscale)
echo.
echo Press any key to exit...
pause > nul
