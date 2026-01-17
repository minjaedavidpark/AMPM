# AMPM
### The Missing Memory Layer for Software Development

*Your SDLC shouldn't have amnesia.*

---

## Quick Start

### 1. Install Dependencies

```bash
# Clone the repo
git clone https://github.com/your-org/AMPM.git
cd AMPM

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for Google Meet)
playwright install chromium

# macOS: Install audio dependencies
brew install portaudio ffmpeg
```

### 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
- **OPENAI_API_KEY** - [platform.openai.com](https://platform.openai.com) (for Whisper STT)
- **CEREBRAS_API_KEY** - [cloud.cerebras.ai](https://cloud.cerebras.ai) (for fast LLM)
- **ELEVENLABS_API_KEY** - [elevenlabs.io](https://elevenlabs.io) (for TTS)

### 3. Run AMPM

**Web App** (recommended for first-time use):
```bash
./run_webapp.sh
```
Access at http://localhost:8501

**Local Voice Bot** (microphone + speakers):
```bash
./run_voice.sh
```

**Google Meet Bot** (join a meeting):
```bash
./run_meeting.sh "https://meet.google.com/abc-defg-hij"
```

> **Note**: All scripts automatically activate the virtual environment. See [SCRIPTS.md](./SCRIPTS.md) for details.

---

## What is AMPM?

AMPM is a **contextual memory system** for software development workflows. It connects meetings, PRDs, Blueprints, Work Orders, and Code in a knowledge graph—so teams can instantly understand WHY decisions were made and see the ripple effects of changes in real-time.

**Two core capabilities:**

1. **Context Retrieval** - Ask "Why did we decide X?" and get an instant answer with sources
2. **Ripple Detection** - Change a PRD and instantly see all downstream artifacts affected

---

## The Problem

As work moves from PRD → Blueprint → Work Order → Code, **context dies**.

- Engineers waste 5-10 hours/week searching for "why"
- Teams build the wrong thing because intent got lost
- Changes upstream don't ripple downstream—until it's too late

---

## Usage

### Web App (Recommended)

```bash
./run_webapp.sh
```

The web interface provides:
- **Ask Questions**: Natural language queries with voice input option
- **Add Info**: Real-time updates during meetings
- **Decision Ledger**: Browse all decisions with search
- **Action Items**: Track tasks by person and status
- **Meeting History**: Full meeting timeline
- **Blockers**: Monitor impediments

Access at http://localhost:8501

### Local Voice Bot

```bash
./run_voice.sh
```

---

## Demo Scenario

**Project**: ShopFlow E-commerce Platform
**Feature**: User Authentication

Ask AMPM:
- *"Why are we using OAuth instead of SAML?"*
- *"What happens if we change the auth requirement?"*
- *"Who decided on Passport.js?"*

**Response time**: ~2 seconds

### Google Meet Bot

**Demo Mode** - Type questions in terminal:
```bash
./run_meeting.sh "https://meet.google.com/abc-defg-hij"
```

**Live Audio Mode** - Listens to meeting audio:
```bash
./run_meeting.sh "https://meet.google.com/abc-defg-hij" --live
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Knowledge Graph | NetworkX |
| Vector Store | FAISS |
| LLM | Cerebras (fast inference) |
| Frontend | Streamlit |

---

## Project Structure

```
AMPM/
├── ampm/                    # Main package
│   ├── core/               # Core functionality
│   │   ├── graph.py        # Meeting knowledge graph
│   │   ├── embeddings.py   # Vector search
│   │   └── query.py        # Natural language queries
│   ├── agents/             # Agent behaviors
│   ├── interfaces/         # User interfaces
│   │   ├── voice_bot.py    # Local voice bot
│   │   └── meet_bot.py     # Google Meet bot
│   └── ingest/             # Data loading
├── data/
│   └── samples/            # Sample meeting data
├── docs/                   # Documentation
│   ├── architecture/
│   └── pitch/
├── tests/
├── app.py                  # Streamlit web app
├── ampm_logo.png           # AMPM logo
├── run.py                  # Run local voice bot
├── run_meet.py             # Run Google Meet bot
├── run_webapp.sh           # Launch web app
├── run_voice.sh            # Launch voice bot
├── run_meeting.sh          # Launch meeting bot
├── test_webapp.sh          # Test webapp setup
├── requirements.txt
├── .env.example
├── README.md
└── SCRIPTS.md              # Run scripts documentation
```

---

## License

MIT

---

*Your SDLC shouldn't have amnesia. We fixed that.*
