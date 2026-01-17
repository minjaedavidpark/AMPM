#!/bin/bash
# AMPM Local Voice Bot - Microphone + speakers
# Usage: ./scripts/run_voice.sh
#
# Say "Hey AMPM" followed by your question

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

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

echo "Starting AMPM Local Voice Bot..."
echo "Say 'Hey AMPM' followed by your question"
echo ""

python run.py
