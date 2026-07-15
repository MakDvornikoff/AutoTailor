@echo off
echo ===================================================
echo   AutoTailor - Windows Automatic Environment Setup
echo ===================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is NOT installed.
    echo Installing Python 3.11 via Windows Package Manager (winget)...
    echo.
    winget install Python.Python.3.11
    if %errorlevel% neq 0 (
        echo.
        echo Failed to install Python automatically.
        echo Please download and install Python manually from: https://www.python.org/downloads/
        echo IMPORTANT: Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Python installed successfully! Please restart this setup script to complete the configuration.
    echo.
    pause
    exit /b 0
) else (
    echo [OK] Python is already installed.
)

:: 2. Check Tesseract-OCR
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        echo Tesseract-OCR is NOT installed.
        echo Installing Tesseract-OCR via winget...
        echo.
        winget install UB-Mannheim.TesseractOCR
        if %errorlevel% neq 0 (
            echo.
            echo Failed to install Tesseract automatically.
            echo Please download and install Tesseract-OCR manually from:
            echo https://github.com/UB-Mannheim/tesseract/wiki
            echo.
        ) else (
            echo [OK] Tesseract-OCR installed successfully!
        )
    ) else (
        echo [OK] Tesseract-OCR detected in default Program Files folder.
    )
) else (
    echo [OK] Tesseract-OCR is already available in PATH.
)

:: 3. Install Python Dependencies
echo.
echo Installing AutoTailor python dependencies...
python -m pip install --upgrade pip
python -m pip install -e .
if %errorlevel% neq 0 (
    echo.
    echo Failed to install python dependencies.
    echo.
) else (
    echo.
    echo [OK] Python dependencies installed successfully!
)

echo.
echo ===================================================
echo   Setup completed! You can now run Process_Inbox.bat
echo ===================================================
echo.
pause
