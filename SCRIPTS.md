# AMPM Run Scripts

Quick-start scripts to run different AMPM components. All scripts automatically activate the virtual environment.

## 📋 Scripts Overview

### 1. Web App (`run_webapp.sh`)
Start the Streamlit web interface for querying meeting history.

```bash
./run_webapp.sh
```

**Features:**
- Query meeting history with natural language
- View decision ledger and action items
- Add information in real-time
- Browse meeting history

**Access:** http://localhost:8501

---

### 2. Voice Bot (`run_voice.sh`)
Run the local voice assistant (microphone + speakers).

```bash
./run_voice.sh
```

**Features:**
- Voice-activated queries ("Hey AMPM...")
- Spoken responses
- Local microphone and speaker interaction

**Requirements:**
- `OPENAI_API_KEY` (for Whisper transcription)
- `ELEVENLABS_API_KEY` (for voice synthesis)
- `CEREBRAS_API_KEY` (for fast LLM responses)

---

### 3. Meeting Bot (`run_meeting.sh`)
Join a Google Meet and answer questions during the meeting.

```bash
# Demo mode (type questions in terminal)
./run_meeting.sh "https://meet.google.com/abc-defg-hij"

# Live audio mode (requires virtual audio routing)
./run_meeting.sh "https://meet.google.com/abc-defg-hij" --live
```

**Modes:**
- **Demo:** Type questions in the terminal, bot responds in the meeting
- **Live:** Bot listens to meeting audio and responds with voice

**Requirements:**
- `CEREBRAS_API_KEY` (for LLM)
- `ELEVENLABS_API_KEY` (for voice synthesis)
- `OPENAI_API_KEY` (for Whisper, live mode only)
- For live mode: Virtual audio routing (e.g., BlackHole on macOS)

---

### 4. Test Script (`test_webapp.sh`)
Validate the webapp setup and dependencies.

```bash
./test_webapp.sh
```

**Checks:**
- Virtual environment exists
- Required dependencies installed
- Required files present
- Python imports work correctly

---

## 🚀 Quick Start

### First Time Setup

1. **Create virtual environment and install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Test the setup:**
   ```bash
   ./test_webapp.sh
   ```

4. **Run the webapp:**
   ```bash
   ./run_webapp.sh
   ```

### Subsequent Runs

Just run the script you need - they handle activation automatically:
```bash
./run_webapp.sh
# or
./run_voice.sh
# or
./run_meeting.sh "<meeting-url>"
```

---

## 🔑 API Keys Required

### For Web App (minimum):
- `OPENAI_API_KEY` - For embeddings and LLM
- OR `CEREBRAS_API_KEY` - For fast LLM (recommended)

### For Voice Features:
- `ELEVENLABS_API_KEY` - For voice synthesis
- `OPENAI_API_KEY` - For Whisper transcription

### Optional:
- `BACKBOARD_API_KEY` - For persistent memory across sessions

Add these to your `.env` file:
```bash
OPENAI_API_KEY=sk-...
CEREBRAS_API_KEY=csk-...
ELEVENLABS_API_KEY=...
BACKBOARD_API_KEY=...  # optional
ELEVENLABS_VOICE_ID=...  # optional, defaults to Rachel
```

---

## 🧪 Testing

### Test the webapp:
```bash
./test_webapp.sh
```

### Manual test (after activation):
```bash
source .venv/bin/activate
python -c "from ampm import MeetingLoader; print('✓ AMPM works')"
streamlit run app.py
```

---

## 🐛 Troubleshooting

### "Virtual environment not found"
The script will create one automatically. If issues persist:
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### "Missing API keys"
Check your `.env` file:
```bash
cat .env
```

Make sure you have the required keys set.

### "Module not found"
Reinstall dependencies:
```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Webapp stuck on "Loading..."
The first run builds the knowledge graph and generates embeddings, which can take 1-2 minutes. Subsequent runs are cached and much faster.

---

## 📝 Notes

- All scripts activate the virtual environment automatically
- Scripts check for dependencies and install if missing
- Logs and errors are displayed in the terminal
- Press Ctrl+C to stop any running script
- The webapp caches data in `.ampm_cache/` for faster subsequent loads
