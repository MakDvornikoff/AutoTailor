@echo off
chcp 65001 > nul
echo {"mode": "color"} > "%~dp0config.json"
echo Output mode set to: COLOR (Clean Color)
echo.
echo Press any key to exit...
pause > nul
