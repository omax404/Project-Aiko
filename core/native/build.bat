@echo off
echo [Aiko Native Helper] Compiling...

where g++ >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Using MinGW g++...
    g++ -std=c++17 -O2 -o aiko_native.exe aiko_native.cpp -lpdh
    if %ERRORLEVEL% == 0 (
        echo [OK] aiko_native.exe compiled with g++
    ) else (
        echo [ERROR] g++ compilation failed
    )
    goto :end
)

where cl >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Using MSVC cl...
    cl /std:c++17 /O2 /Fe:aiko_native.exe aiko_native.cpp pdh.lib
    if %ERRORLEVEL% == 0 (
        echo [OK] aiko_native.exe compiled with MSVC
    ) else (
        echo [ERROR] MSVC compilation failed
    )
    goto :end
)

echo [ERROR] No compiler found. Install MinGW (g++) or Visual Studio (cl).
echo         Download MinGW: https://www.mingw-w64.org/

:end
pause
