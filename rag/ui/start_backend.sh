#!/bin/bash
# Start script for SmartBeauty AI Chatbot Backend

echo "🚀 Starting SmartBeauty AI Chatbot Backend..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the ui/ directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "../../../venv" ] && [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python -m venv venv
    echo "✅ Virtual environment created."
fi

# Activate virtual environment
if [ -d "../../../venv" ]; then
    echo "📦 Activating virtual environment..."
    source ../../../venv/bin/activate 2>/dev/null || source ../../../venv/Scripts/activate
elif [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
fi

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=true

# Add the core directory to Python path
export PYTHONPATH="${PYTHONPATH}:../core"

echo "📡 Starting Flask server on http://127.0.0.1:5000"
echo "💡 Open your browser and navigate to http://127.0.0.1:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the Flask app
python app.py
