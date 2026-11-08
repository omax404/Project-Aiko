@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Project Aiko v2.0 - One-Click Windows Installer
cd /d "%~dp0"

echo.
echo  ============================================================
echo     PROJECT AIKO v2.0 - ONE-CLICK WINDOWS SETUP
echo     Live2D Companion + Voice + Vision + Memory Palace
echo  ============================================================
echo.

:: 1. Check Python 3.11+
echo  [1/6] Checking Python runtime...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [!] Python not found on PATH. Attempting automatic install via winget...
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% neq 0 (
        echo  [ERROR] Could not auto-install Python. Please install Python 3.11+ from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
)
echo        OK - Python detected.

:: 2. Create & populate .venv
echo  [2/6] Setting up isolated Python environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo  [ERROR] Failed to create .venv virtual environment.
        pause
        exit /b 1
    )
)

echo  [3/6] Installing & verifying Aiko neural dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel -q
if exist "requirements.lock" (
    ".venv\Scripts\python.exe" -m pip install -r requirements.lock -q
    if %ERRORLEVEL% neq 0 (
        ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
    )
) else (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
)
echo ready > ".venv\.ready"
echo        OK - Python dependencies ready.

:: 4. Initialize configuration files if missing
echo  [4/6] Verifying configuration & data directories...
if not exist "data" mkdir "data"
if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\voices" mkdir "data\voices"
if not exist ".logs" mkdir ".logs"

if not exist ".env" (
    if exist ".env.example" copy /y ".env.example" ".env" >nul
)
if not exist "user_settings.json" (
    if exist "user_settings.example.json" copy /y "user_settings.example.json" "user_settings.json" >nul
)
echo        OK - Configuration initialized.

:: 5. Create Desktop & Start Menu Shortcuts with Aiko Icon
echo  [5/6] Creating Desktop and Start Menu shortcuts...
set "TARGET_BAT=%~dp0LAUNCH_AIKO.bat"
set "ICON_PATH=%~dp0aiko-app\src-tauri\icons\icon.ico"
set "DESKTOP_LNK=%USERPROFILE%\Desktop\Aiko Companion.lnk"
set "STARTMENU_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Aiko Companion.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   foreach ($p in @('%DESKTOP_LNK%', '%STARTMENU_LNK%')) { ^
     $s = $ws.CreateShortcut($p); ^
     $s.TargetPath = '%TARGET_BAT%'; ^
     $s.WorkingDirectory = '%~dp0'; ^
     $s.Description = 'Launch Aiko AI Desktop Companion'; ^
     if (Test-Path '%ICON_PATH%') { $s.IconLocation = '%ICON_PATH%' }; ^
     $s.Save() ^
   }" >nul 2>&1
echo        OK - Shortcuts created on Desktop and Start Menu ("Aiko Companion").

:: 6. Run Preflight Check
echo  [6/6] Running preflight health diagnostics...
".venv\Scripts\python.exe" launch.py --check

echo.
echo  ============================================================
echo     INSTALLATION COMPLETE!
echo     Shortcut created: Desktop\Aiko Companion
echo     Starting Aiko now...
echo  ============================================================
echo.
call "%~dp0LAUNCH_AIKO.bat"
