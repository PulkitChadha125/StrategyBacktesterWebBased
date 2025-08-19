@echo off
echo Setting up Strategy Backtester environment...
echo.

echo Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo.
echo To run the application:
echo 1. Activate the virtual environment: .venv\Scripts\activate
echo 2. Run the app: streamlit run app.py
echo.
echo Or simply double-click this file again to run the app directly.
echo.

set /p choice="Would you like to run the app now? (y/n): "
if /i "%choice%"=="y" (
    echo Starting Strategy Backtester...
    streamlit run app.py
) else (
    echo Setup complete. You can run the app later with: streamlit run app.py
)

pause
