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
└── README.md
```

---

## Sample Data

AMPM comes with sample meeting data from a fictional project:

**Project**: ShopFlow E-commerce Platform
**Team**: Sarah (PM), Mike (CTO), Bob (Eng Lead), Alice (Design)
**Timeline**: May 1-9, 2026

**Key Events**:
- Sprint Planning: Decided to use Stripe over Braintree
- Legal approval blocker (took 8 days instead of 3)
- Leadership escalation resolved the blocker

Try asking:
- *"Why did we choose Stripe?"*
- *"What happened with Legal?"*
- *"Who approved the payment integration?"*

---

## API Reference

### AMPMBot

```python
from ampm import AMPMBot

bot = AMPMBot()

# Ask a question (text only)
response = bot.ask("Why did we choose Stripe?")
print(response)

# Ask and speak the response
response = bot.ask_and_speak("Who made the checkout decision?")

# Run interactive loop
bot.run()
```

### MeetingKnowledge

```python
from ampm import MeetingKnowledge

# Load custom meeting data
knowledge = MeetingKnowledge("path/to/meetings.json")

# Get context for LLM
context = knowledge.get_context()
print(f"Project: {knowledge.project_name}")
print(f"Meetings: {knowledge.meeting_count}")
```

### Google Meet Bots

```python
import asyncio
from ampm import DemoMeetBot, MeetBot

# Demo mode (type questions)
bot = DemoMeetBot("https://meet.google.com/xxx-xxxx-xxx")
asyncio.run(bot.start())

# Live audio mode
bot = MeetBot("https://meet.google.com/xxx-xxxx-xxx")
asyncio.run(bot.start())
```

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Speech-to-Text** | OpenAI Whisper | Accurate, multilingual |
| **LLM** | Cerebras (Llama 3.3 70B) | Ultra-fast inference (~0.4s) |
| **Text-to-Speech** | ElevenLabs | Natural voice quality |
| **Browser Automation** | Playwright | Reliable Google Meet integration |
| **Audio I/O** | sounddevice | Cross-platform audio |

---

## Troubleshooting

### "No audio input devices"
- Check your microphone is connected
- On macOS, grant terminal microphone permission in System Preferences

### "Cerebras connection failed"
- Verify your `CEREBRAS_API_KEY` is correct
- Check your internet connection

### "ElevenLabs error"
- Verify your `ELEVENLABS_API_KEY` is correct
- Check you have remaining character quota

### Audio echo/feedback in meetings
- Use headphones instead of speakers
- The bot pauses listening while speaking

### Bot audio not heard in meeting
**The bot needs virtual audio routing to speak in Google Meet.**

The bot plays audio through your system, but Google Meet needs to receive it through a microphone input. You need to route the bot's audio output to a virtual microphone that Google Meet can use.

**macOS Setup (Recommended):**
1. Install BlackHole: `brew install blackhole-2ch` or download from [GitHub](https://github.com/ExistentialAudio/BlackHole)
2. Open **Audio MIDI Setup** (Applications → Utilities)
3. Click **+** → **Create Multi-Output Device**
4. Check both:
   - ✅ **Built-in Output** (so you can still hear)
   - ✅ **BlackHole 2ch** (so Google Meet can capture)
5. Set this Multi-Output Device as your **System Output** (System Preferences → Sound → Output)
6. In Google Meet, go to Settings → Audio
7. Set **Microphone** to **BlackHole 2ch**
8. Now when the bot speaks, audio goes: Bot → BlackHole → Google Meet mic ✅

**Windows Setup:**
1. Install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
2. Set it as your default playback device
3. In Google Meet settings, set microphone to "VB-Audio Virtual Cable"

**Linux Setup:**
1. Install PulseAudio: `sudo apt install pulseaudio`
2. Create loopback: `pactl load-module module-loopback`
3. Configure Google Meet to use loopback as microphone

### Google Meet "can't join meeting"
- You need to be invited to the meeting
- Log into the correct Google account when prompted
- Consider using a separate Google account for the bot

---

## The Vision

### The Problem

Product teams have meetings all day. Critical decisions happen. Action items are assigned.

**Then it all disappears.**

- **23 hours/month** per person in meetings (Atlassian 2024)
- **40% of that time** wasted due to lack of context (HBR)
- **Critical knowledge** walks out the door when PMs leave

### The Solution

AMPM builds a **living memory** of your product decisions:

- **Decision Memory**: "Why did we decide that?" → Instant answer with full context
- **Cross-Meeting Tracking**: Follow action items across all meetings
- **New PM Onboarding**: Day 1 productivity instead of week 3
- **Meeting ROI**: Data-driven meeting optimization

---

## License

MIT

---

*Your SDLC shouldn't have amnesia. We fixed that.*
