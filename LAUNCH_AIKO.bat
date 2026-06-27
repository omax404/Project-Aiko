@echo off
if "%1"=="h" goto :run_hidden

echo Set WshShell = CreateObject("WScript.Shell") > "%temp%\launcher_hidden.vbs"
echo WshShell.Run """%~dp0LAUNCH_AIKO.bat"" h", 0, False >> "%temp%\launcher_hidden.vbs"
wscript.exe "%temp%\launcher_hidden.vbs"
exit /b

:run_hidden
setlocal enabledelayedexpansion
title Aiko Core Launcher
mode con: cols=90 lines=28
color 0D

:: Premium Visual Header
echo ==========================================================================================
echo               ___   ___  _  __ ___     ___   ___   ___   ___ 
echo              / _ \ / _ \(_)/ /_/ _ \   / _ \ / _ \ / _ \ / _ \
echo             / _  // // // //  __/ // /  / // // // // / _  // // /
echo            /_/ \_\/_//_//_//_/  /\___/  /\___/ \___//_/ \_\/\___/ 
echo.
echo                       - N E U R A L   C O M P A N I O N -
echo ==========================================================================================
echo.

:: Search for python interpreter to avoid Windows Store app execution alias redirect trap.
set "PYTHON_CMD="

:: 1. Check local virtual environment first
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
    goto :found_python
)

:: 2. Check if 'py' launcher is available
where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :found_python
)

:: 3. Check if standard python in PATH doesn't point to Microsoft WindowsApps redirect stub
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    set "p=%%i"
    if "!p:WindowsApps=!"=="!p!" (
        set "PYTHON_CMD=%%i"
        goto :found_python
    )
)

:: 4. Check typical installation directory under Local AppData
for /d %%d in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_CMD=%%d\python.exe"
        goto :found_python
    )
)

:: 5. Check typical installation directory under Program Files
for /d %%d in ("%SystemDrive%\Program Files\Python*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_CMD=%%d\python.exe"
        goto :found_python
    )
)
for /d %%d in ("%SystemDrive%\Program Files (x86)\Python*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_CMD=%%d\python.exe"
        goto :found_python
    )
)

:: 6. Fallback to just python and hope it works
set "PYTHON_CMD=python"

:found_python
echo [System] Selected Python interpreter: "%PYTHON_CMD%"

:: Run launcher script
"%PYTHON_CMD%" "%~dp0launch.py"

if %errorlevel% neq 0 (
    echo.
    echo [Error] Neural Link launcher exited with error code %errorlevel%.
    echo.
    pause
)
