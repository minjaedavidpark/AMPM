#!/bin/bash
# AMPM Voice Bot Launcher
# Activates virtual environment and starts local voice bot

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🕐 Starting AMPM Voice Bot..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import ampm" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Copy .env.example to .env and add your API keys"
    exit 1
fi

# Start voice bot
echo "🚀 Starting voice bot (microphone + speakers)..."
echo "   Say 'Hey AMPM' followed by your question"
echo ""
python run.py
