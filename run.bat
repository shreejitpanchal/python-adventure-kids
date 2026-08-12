@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ============================================
    echo   Setting up Python Adventure for the
    echo   first time. This only happens once and
    echo   may take a minute...
    echo ============================================
    echo.

    where python >nul 2>nul
    if errorlevel 1 (
        echo Python was not found on this computer.
        echo Please install Python from https://python.org
        echo then run this file again.
        echo.
        pause
        exit /b 1
    )

    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo Something went wrong creating the Python environment.
        echo.
        pause
        exit /b 1
    )

    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Something went wrong installing the required packages.
        echo.
        pause
        exit /b 1
    )

    echo.
    echo Setup complete!
    echo.
)

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "main.py"
) else (
    start "" ".venv\Scripts\python.exe" "main.py"
)
