@echo off
REM Cruise Logs - Main Form Launcher
REM This batch file activates the conda environment and starts the cruise form

echo ========================================
echo Cruise Logs - Starting Main Form
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

REM Check if cruise_form.py exists
if not exist "cruise_form.py" (
    echo ERROR: cruise_form.py not found in C:\Cruise_Logs
    pause
    exit /b 1
)

REM Start Streamlit
echo Starting Streamlit application...
echo.
echo The application will open in your default browser.
echo To stop the server, press Ctrl+C in this window.
echo.
streamlit run cruise_form.py

REM If streamlit exits, pause to show any error messages
if errorlevel 1 (
    echo.
    echo ERROR: Streamlit encountered an error
    pause
)
