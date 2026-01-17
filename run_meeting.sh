#!/bin/bash
# AMPM Meeting Bot Launcher
# Activates virtual environment and starts Google Meet bot

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🕐 Starting AMPM Meeting Bot..."
echo ""

# Check arguments
if [ "$#" -lt 1 ]; then
    echo "Usage:"
    echo "  ./run_meeting.sh <meeting_url>           # Demo mode (type questions)"
    echo "  ./run_meeting.sh <meeting_url> --live    # Live audio mode"
    echo ""
    echo "Example:"
    echo "  ./run_meeting.sh 'https://meet.google.com/abc-defg-hij'"
    exit 1
fi

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

# Start meeting bot
echo "🚀 Joining meeting: $1"
if [[ "$*" == *"--live"* ]]; then
    echo "   Mode: LIVE AUDIO"
    echo "   Note: Requires virtual audio routing (e.g., BlackHole on macOS)"
else
    echo "   Mode: DEMO (type questions in terminal)"
fi
echo ""
python run_meet.py "$@"
