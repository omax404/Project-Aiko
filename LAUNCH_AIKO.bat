@echo off
title Aiko Desktop Launcher
setlocal enabledelayedexpansion

echo.
echo  💖 AIKO DESKTOP - NEURAL LINK INITIALIZER 🌸
echo ----------------------------------------------

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed! 
    echo Please download Python from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

:: 2. Check for Virtual Environment
if not exist ".venv" (
    echo [INFO] Creating neural environment (this only happens once)...
    python -m venv .venv
)

:: 3. Activate and Install Requirements
echo [INFO] Warming up neural modules...
call .venv\Scripts\activate

:: Check if requirements are installed (look for a marker file)
if not exist ".venv\.ready" (
    echo [INFO] Installing required libraries...
    pip install -r requirements.txt
    if %errorlevel% equ 0 (
        echo Done > .venv\.ready
    ) else (
        echo [ERROR] Failed to install dependencies. Please check your internet connection.
        pause
        exit /b
    )
)

:: 4. Launch the App
echo [SUCCESS] Neural Link Stable. Launching Aiko...
python start_aiko_tauri.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Aiko closed unexpectedly.
    pause
)
