@echo off
REM Cruise_Logs Windows Installer Wrapper
REM This batch file runs the PowerShell installer script
REM Right-click and select "Run as Administrator"

setlocal enabledelayedexpansion

REM Color codes
for /F %%A in ('echo prompt $H ^| cmd') do set "BS=%%A"

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo =========================================
    echo ERROR: Administrator privileges required!
    echo =========================================
    echo.
    echo Please right-click this file and select:
    echo "Run as Administrator"
    echo.
    pause
    exit /b 1
)

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%install.ps1"

REM Check if PowerShell script exists
if not exist "%PS_SCRIPT%" (
    echo.
    echo =========================================
    echo ERROR: install.ps1 not found!
    echo =========================================
    echo.
    echo Expected location: %PS_SCRIPT%
    echo.
    pause
    exit /b 1
)

REM Display banner
echo.
echo ╔════════════════════════════════════════════════════╗
echo ║   Cruise_Logs Windows Installer                   ║
echo ║   Starting installation wizard...                 ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if errorlevel 1 (
    echo ERROR: PowerShell not found. This script requires PowerShell.
    pause
    exit /b 1
)

REM Run the PowerShell script
REM Set execution policy for this process and run the installer
echo Running PowerShell installer...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"

REM Capture exit code
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE% equ 0 (
    echo.
    echo ╔════════════════════════════════════════════════════╗
    echo ║   Installation wrapper completed successfully!    ║
    echo ╚════════════════════════════════════════════════════╝
) else (
    echo.
    echo ╔════════════════════════════════════════════════════╗
    echo ║   Installation wrapper exited with code: %EXIT_CODE% ║
    echo ╚════════════════════════════════════════════════════╝
)

endlocal
exit /b %EXIT_CODE%
