# AMPM
### AI Meeting Product Manager
*From AM to PM, Never Miss a Decision*

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

**Local Voice Bot** (microphone + speakers):
```bash
python run.py
```

**Google Meet Bot** (join a meeting):
```bash
python run_meet.py "https://meet.google.com/abc-defg-hij"
```

---

## What is AMPM?

**"Why did we decide that?" shouldn't take 3 hours to answer.**

AMPM is an AI meeting assistant that:
1. **Captures** decisions, action items, and context from meetings
2. **Remembers** everything across all your meetings
3. **Answers** questions about past decisions instantly

### How It Works

```
Voice Input → Whisper STT → Cerebras LLM → ElevenLabs TTS → Voice Output
                              ↑
                       Meeting History
```

**Performance**: ~2 seconds total response time
- Cerebras LLM: ~0.4s
- ElevenLabs TTS: ~1.5s

---

## Usage

### Local Voice Bot

```bash
python run.py
```

Say "Hey AMPM" followed by your question:
- *"Hey AMPM, why did we choose Stripe?"*
- *"AMPM, what happened with Legal approval?"*
- *"Hey AMPM, who made the checkout decision?"*

Press `Ctrl+C` to stop.

### Google Meet Bot

**Demo Mode** - Type questions in terminal:
```bash
python run_meet.py "https://meet.google.com/abc-defg-hij"
```

**Live Audio Mode** - Listens to meeting audio:
```bash
python run_meet.py "https://meet.google.com/abc-defg-hij" --live
```

> **Note**: Live mode requires virtual audio routing (e.g., BlackHole on macOS).

---

## Project Structure

```
AMPM/
├── ampm/                    # Main package
│   ├── __init__.py
│   ├── bot.py              # Local voice bot
│   ├── knowledge.py        # Meeting knowledge base
│   └── meet_bot.py         # Google Meet integration
├── data/
│   └── sample_meetings.json # Sample meeting data
├── docs/                    # Documentation
│   ├── architecture/
│   ├── pitch/
│   └── demo/
├── tests/
├── run.py                   # Run local bot
├── run_meet.py              # Run Google Meet bot
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

MIT License

---

**AMPM: AI Meeting Product Manager**

*From AM to PM, Never Miss a Decision*
