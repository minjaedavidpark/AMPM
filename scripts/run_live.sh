#!/bin/bash
# AMPM Live Meet Bot - Listens to meeting audio
# Usage: ./scripts/run_live.sh <meeting_url>
# Example: ./scripts/run_live.sh "https://meet.google.com/abc-defg-hij"
#
# Note: Requires virtual audio routing (e.g., BlackHole on macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check for meeting URL
if [ -z "$1" ]; then
    echo "Usage: $0 <google_meet_url>"
    echo "Example: $0 'https://meet.google.com/abc-defg-hij'"
    exit 1
fi

MEETING_URL="$1"

# Validate URL
if [[ ! "$MEETING_URL" =~ ^https://meet\.google\.com/ ]]; then
    echo "Error: Invalid Google Meet URL"
    echo "URL should look like: https://meet.google.com/abc-defg-hij"
    exit 1
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: No virtual environment found. Run: python3 -m venv .venv && pip install -r requirements.txt"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check required API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY required for Whisper transcription"
    exit 1
fi

if [ -z "$CEREBRAS_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: Missing LLM API key. Set CEREBRAS_API_KEY or OPENAI_API_KEY in .env"
    exit 1
fi

if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "Warning: ELEVENLABS_API_KEY not set - voice responses will be disabled"
fi

echo "Starting AMPM Live Meet Bot..."
echo "Meeting: $MEETING_URL"
echo ""
echo "Note: Use headphones to prevent audio feedback!"
echo ""

python run_meet.py "$MEETING_URL" --live
