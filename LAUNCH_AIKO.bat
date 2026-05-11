@echo off
title Aiko Desktop - Neural Link Initializer
setlocal enabledelayedexpansion
color 0F

echo.
echo  ============================================
echo   AIKO DESKTOP - NEURAL LINK INITIALIZER
echo  ============================================
echo.

:: ── 1. Check for Python ──────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not installed!
    echo.
    echo  Please download Python from https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  [OK] %PYVER%

:: ── 2. Check for Node.js ─────────────────────────────
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!!] Node.js not found.
    echo  [!!] Install from: https://nodejs.org/ (LTS recommended)
    echo  [!!] Aiko will run in browser-fallback mode.
    echo.
) else (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODEVER=%%i
    echo  [OK] Node.js !NODEVER!
)

:: ── 3. Create Virtual Environment if needed ──────────
if not exist ".venv" (
    echo.
    echo  [INFO] Creating neural environment (first time only)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to create virtual environment.
        echo  Try running: python -m ensurepip --upgrade
        pause
        exit /b
    )
)

:: ── 4. Activate and Install Requirements ─────────────
echo  [INFO] Warming up neural modules...
call .venv\Scripts\activate

if not exist ".venv\.ready" (
    echo  [INFO] Installing required libraries (first time only, ~2 min)...
    pip install -r requirements.txt -q
    if %errorlevel% equ 0 (
        echo Done > .venv\.ready
        echo  [OK] Dependencies installed.
    ) else (
        echo.
        echo  [ERROR] Failed to install dependencies.
        echo  Check your internet connection and try again.
        pause
        exit /b
    )
) else (
    echo  [OK] Dependencies ready.
)

:: ── 5. Launch Aiko ───────────────────────────────────
echo.
echo  [SUCCESS] Neural Link Stable. Launching Aiko...
echo.
python start_aiko_tauri.py

if %errorlevel% neq 0 (
    echo.
    echo  ============================================
    echo   Aiko closed unexpectedly.
    echo   Check .logs\neural_hub.log for details.
    echo  ============================================
    echo.
    pause
)
