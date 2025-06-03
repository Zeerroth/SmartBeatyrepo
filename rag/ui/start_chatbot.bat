@echo off
echo ========================================
echo   SmartBeauty AI Chatbot Startup
echo ========================================
echo.

:: Check if we're in the right directory
if not exist "app.py" (
    echo Error: app.py not found in current directory
    echo Please run this script from the ui folder
    pause
    exit /b 1
)

:: Set environment variables for SSL (Windows fix)
set SSL_CERT_FILE=
set SSL_CERT_DIR=
set REQUESTS_CA_BUNDLE=

echo Starting SmartBeauty AI Chatbot...
echo.
echo The chatbot will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

:: Run the Flask app
python app.py

pause
