@echo off
echo ========================================
echo German30 Trading Simulator
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Run the application
echo Starting Flask server...
echo.
echo Access the application at: http://localhost:5000
echo Press CTRL+C to stop the server
echo.
python app.py

pause
