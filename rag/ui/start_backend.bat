@echo off
REM Start script for SmartBeauty AI Chatbot Backend (Windows)

echo 🚀 Starting SmartBeauty AI Chatbot Backend...

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: app.py not found. Please run this script from the ui\ directory.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "..\..\..\venv" if not exist "venv" (
    echo ⚠️  Virtual environment not found. Creating one...
    python -m venv venv
    echo ✅ Virtual environment created.
)

REM Activate virtual environment
if exist "..\..\..\venv" (
    echo 📦 Activating virtual environment...
    call ..\..\..\venv\Scripts\activate.bat
) else if exist "venv" (
    echo 📦 Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install requirements
echo 📦 Installing requirements...
pip install -r requirements.txt

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=true

REM Add the core directory to Python path
set PYTHONPATH=%PYTHONPATH%;..\core

echo 📡 Starting Flask server on http://127.0.0.1:5000
echo 💡 Open your browser and navigate to http://127.0.0.1:5000
echo 🛑 Press Ctrl+C to stop the server
echo.

REM Start the Flask app
python app.py

pause
