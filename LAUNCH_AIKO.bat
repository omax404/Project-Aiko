@echo off
title Aiko Desktop - Neural Link Initializer
color 0F

echo.
echo  ============================================
echo   AIKO DESKTOP - NEURAL LINK INITIALIZER
echo  ============================================
echo.

REM ── 1. Check for Python ──────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed!
    echo.
    echo  Please download Python from https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "PYVER=%%i"
echo  [OK] %PYVER%

REM ── 2. Check for Node.js ─────────────────────────────
set "HAS_NODE=0"
where node >nul 2>&1
if errorlevel 1 (
    echo  [!!] Node.js not found.
    echo  [!!] Aiko will run in browser-fallback mode.
    echo.
) else (
    set "HAS_NODE=1"
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do set "NODEVER=%%i"
)
if "%HAS_NODE%"=="1" echo  [OK] Node.js %NODEVER%

REM ── 3. Create Virtual Environment if needed ──────────
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo  [INFO] Creating neural environment (first time only)...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        echo  Try running: python -m ensurepip --upgrade
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created.
)

REM ── 4. Activate and Install Requirements ─────────────
echo  [INFO] Warming up neural modules...
call .venv\Scripts\activate.bat

if not exist ".venv\.ready" (
    echo  [INFO] Installing required libraries (first time only)...
    echo  [INFO] This may take 2-5 minutes depending on your internet speed.
    echo.
    pip install -r requirements.txt -q --no-warn-script-location 2>&1
    if errorlevel 1 (
        echo.
        echo  [ERROR] Some dependencies failed to install.
        echo  [INFO]  This is often caused by missing build tools.
        echo.
        echo  Try these fixes:
        echo    1. pip install --upgrade pip setuptools wheel
        echo    2. Install Visual C++ Build Tools from:
        echo       https://visualstudio.microsoft.com/visual-cpp-build-tools/
        echo    3. Try Python 3.11 instead of 3.13 for best compatibility.
        echo.
        pause
        exit /b 1
    )
    echo Done > .venv\.ready
    echo  [OK] Dependencies installed.
) else (
    echo  [OK] Dependencies ready.
)

REM ── 5. Launch Aiko ───────────────────────────────────
echo.
echo  ============================================
echo   Neural Link Stable. Launching Aiko...
echo  ============================================
echo.
python start_aiko_tauri.py

if errorlevel 1 (
    echo.
    echo  ============================================
    echo   Aiko exited with an error.
    echo   Check .logs\neural_hub.log for details.
    echo  ============================================
    echo.
)

echo.
echo  Press any key to exit...
pause >nul
