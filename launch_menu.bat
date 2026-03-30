@echo off
REM Cruise Logs - Application Launcher
REM Launches the modern GUI menu for selecting Cruise Logs applications

echo ========================================
echo Cruise Logs - Application Launcher
echo ========================================
echo.

REM Activate conda environment
echo Activating base environment...
call conda activate base
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment 'base'
    echo Please ensure conda is installed properly
    pause
    exit /b 1
)

REM Change to Cruise_Logs directory
echo Changing to C:\Cruise_Logs...
cd /d C:\Cruise_Logs
if errorlevel 1 (
    echo ERROR: Could not find C:\Cruise_Logs directory
    pause
    exit /b 1
)

REM Check if launcher.py exists
if not exist "launcher.py" (
    echo ERROR: launcher.py not found in C:\Cruise_Logs
    pause
    exit /b 1
)

REM Check if customtkinter is installed
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo CustomTkinter not installed. Installing now...
    pip install customtkinter
    if errorlevel 1 (
        echo ERROR: Failed to install customtkinter
        pause
        exit /b 1
    )
)

REM Start the launcher
echo Starting Cruise Logs Launcher...
echo.
python launcher.py

REM If launcher exits with error, show message
if errorlevel 1 (
    echo.
    echo ERROR: Launcher encountered an error
    pause
)
