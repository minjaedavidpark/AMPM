#!/bin/bash
# AMPM Test Suite
# Usage: ./scripts/run_tests.sh

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

echo "=========================================="
echo "AMPM Test Suite"
echo "=========================================="
echo ""

# Test 1: Knowledge Graph
echo "=== Test 1: Knowledge Graph ==="
python3 -c "
from ampm.core.graph import MeetingGraph
from ampm.core.embeddings import EmbeddingStore
from ampm.ingest.loader import MeetingLoader

graph = MeetingGraph()
embeddings = EmbeddingStore(use_backboard=False)
loader = MeetingLoader(graph, embeddings)

# Load one sample file
loader.load_file('data/samples/sprint_planning_2026_05_01.json')
stats = graph.stats
print(f'  Meetings: {stats[\"meetings\"]}')
print(f'  Decisions: {stats[\"decisions\"]}')
print(f'  Action Items: {stats[\"action_items\"]}')
print(f'  People: {stats[\"people\"]}')
print('  Knowledge Graph: OK')
"
echo ""

# Test 2: Backboard Connection
echo "=== Test 2: Backboard Connection ==="
if [ -z "$BACKBOARD_API_KEY" ]; then
    echo "  Skipped (BACKBOARD_API_KEY not set)"
else
    python3 -c "
from ampm.core.embeddings import EmbeddingStore
import os

store = EmbeddingStore(use_backboard=True, config_dir='.ampm')
if store.thread_id:
    print(f'  Thread: {store.thread_id[:8]}...')
    print('  Backboard: OK')
else:
    print('  Backboard: Failed to connect')
"
fi
echo ""

# Test 3: Query Engine
echo "=== Test 3: Query Engine ==="
python3 -c "
from ampm.core.graph import MeetingGraph
from ampm.core.embeddings import EmbeddingStore
from ampm.core.query import QueryEngine
from ampm.ingest.loader import MeetingLoader

graph = MeetingGraph()
embeddings = EmbeddingStore(use_backboard=False)
loader = MeetingLoader(graph, embeddings)
loader.load_file('data/samples/sprint_planning_2026_05_01.json')

engine = QueryEngine(graph, embeddings)
result = engine.query('What decisions were made?')
if result.answer:
    print(f'  Answer length: {len(result.answer)} chars')
    print(f'  Query time: {result.query_time_ms:.0f}ms')
    print('  Query Engine: OK')
else:
    print('  Query Engine: Failed')
"
echo ""

# Test 4: Semantic Search (if Backboard available)
echo "=== Test 4: Semantic Search ==="
if [ -z "$BACKBOARD_API_KEY" ]; then
    echo "  Skipped (BACKBOARD_API_KEY not set)"
else
    python3 -c "
from ampm.core.embeddings import EmbeddingStore

store = EmbeddingStore(use_backboard=True, config_dir='.ampm')
if store.thread_id:
    results = store.search('payment decisions', top_k=3)
    print(f'  Results found: {len(results)}')
    print('  Semantic Search: OK')
else:
    print('  Semantic Search: Skipped (no thread)')
"
fi
echo ""

echo "=========================================="
echo "All tests completed!"
echo "=========================================="
