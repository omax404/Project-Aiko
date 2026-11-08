@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
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

:: ---------------------------------------------------------------------------
:: Free the ports Aiko needs (8000 = brain, 1422 = interface) so it never ends
:: up on 8001 talking to an old copy. Only python / node / aiko-app processes
:: are ever closed; anything else is left alone.
:: ---------------------------------------------------------------------------
echo [System] Checking ports 8000 and 1422...
call :free_ports
call :port_busy 8000
if "!BUSY!"=="1" (
    net session >nul 2>&1
    if errorlevel 1 (
        if /I not "%~1"=="elev" (
            echo [System] An old Aiko process still holds port 8000 and needs administrator rights to close.
            echo [System] Windows will ask for permission - click Yes.
            powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList 'elev' -Verb RunAs"
            exit /b 0
        )
    )
    call :free_ports
    call :port_busy 8000
    if "!BUSY!"=="1" (
        echo.
        echo [Error] Port 8000 is still in use by a program that is not Aiko.
        echo         Find it with:  netstat -ano ^| findstr :8000
        echo.
        pause
        exit /b 1
    )
)
echo [System] Ports are free.
echo.

:: Run launcher script (this window stays open so any error is visible)
"%PYTHON_CMD%" "%~dp0launch.py"

if %errorlevel% neq 0 (
    echo.
    echo [Error] Neural Link launcher exited with error code %errorlevel%.
    echo.
    pause
)
endlocal
exit /b 0

:: ---------------------------------------------------------------------------
:port_busy
set "BUSY=0"
netstat -ano | findstr /R /C:":%~1 .*LISTENING" >nul 2>&1 && set "BUSY=1"
exit /b 0

:free_ports
taskkill /F /IM aiko-app.exe /T >nul 2>&1
powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; foreach($port in 8000,1422){ Get-NetTCPConnection -LocalPort $port -State Listen | ForEach-Object { $p = Get-Process -Id $_.OwningProcess; if ($p -and ($p.ProcessName -in 'python','node','aiko-app')) { Stop-Process -Id $p.Id -Force } } }" >nul 2>&1
timeout /t 1 /nobreak >nul
exit /b 0
