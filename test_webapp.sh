#!/bin/bash
# AMPM Web App Test Script
# Tests the webapp by starting it and running basic checks

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🧪 Testing AMPM Web App..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
source .venv/bin/activate

# Check dependencies
echo "Checking dependencies..."
if ! python -c "import streamlit" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Using .env.example for reference"
fi

# Check required files
echo "Checking required files..."
FILES=("app.py" "ampm_logo.png" "data/samples" "ampm/__init__.py")
for file in "${FILES[@]}"; do
    if [ ! -e "$file" ]; then
        echo "❌ Missing: $file"
        exit 1
    fi
    echo "✓ Found: $file"
done

# Test Python imports
echo ""
echo "Testing Python imports..."
python -c "
import sys
try:
    from ampm import MeetingLoader, QueryEngine, MeetingGraph
    print('✓ AMPM modules import successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

try:
    import streamlit
    print('✓ Streamlit import successful')
except ImportError as e:
    print(f'❌ Streamlit import error: {e}')
    sys.exit(1)
"

echo ""
echo "✅ All checks passed!"
echo ""
echo "To start the webapp:"
echo "  ./run_webapp.sh"
echo ""
echo "Or manually:"
echo "  source .venv/bin/activate"
echo "  streamlit run app.py"
