# AMPM
### The Missing Memory Layer for Software Development

*Your SDLC shouldn't have amnesia.*

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

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and CEREBRAS_API_KEY

# Run the app
python run_webapp.sh
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
├── ampm/           # Main package
├── data/           # Sample data
├── docs/           # Documentation
│   ├── pitch/      # Pitch guide
│   ├── demo/       # Demo script
│   └── architecture/
└── samples/        # Example code
```

---

## License

MIT

---

*Your SDLC shouldn't have amnesia. We fixed that.*
