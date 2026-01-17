# AMPM - Architecture
### Technical Architecture Overview

---

## Vision

AMPM is a **contextual memory layer** for software development that:
- Connects PRDs, Blueprints, Work Orders, and Code in a knowledge graph
- Answers "Why does this exist?" in seconds with sources
- Detects ripple effects when requirements change

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                       AMPM                           │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │              STREAMLIT UI                    │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────┐   │    │
│  │  │ Context │ │ Ripple  │ │  Artifact   │   │    │
│  │  │  Query  │ │Detection│ │  Explorer   │   │    │
│  │  └─────────┘ └─────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────┘    │
│                        │                            │
│  ┌─────────────────────────────────────────────┐    │
│  │            INTELLIGENCE LAYER                │    │
│  │  ┌──────────────┐  ┌──────────────────┐     │    │
│  │  │ Query Engine │  │ Ripple Detector  │     │    │
│  │  │ (LLM + RAG)  │  │ (Parallel LLM)   │     │    │
│  │  └──────────────┘  └──────────────────┘     │    │
│  └─────────────────────────────────────────────┘    │
│                        │                            │
│  ┌─────────────────────────────────────────────┐    │
│  │              DATA LAYER                      │    │
│  │  ┌──────────────┐  ┌──────────────────┐     │    │
│  │  │Knowledge Graph│  │ Vector Embeddings│     │    │
│  │  │  (NetworkX)  │  │    (FAISS)       │     │    │
│  │  └──────────────┘  └──────────────────┘     │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Knowledge Graph Schema

```
PRD
 ├── Decisions (with rationale)
 └── Requirements
      └── Blueprint
           ├── Architecture Decisions
           └── Technical Specs
                └── Work Orders
                     ├── Assigned To
                     └── Status
```

### Node Types

| Node | Description |
|------|-------------|
| **PRD** | Product requirements document |
| **Blueprint** | Technical architecture/design doc |
| **WorkOrder** | Implementation task |
| **Decision** | A choice made (with rationale, author, timestamp) |
| **Person** | Author, assignee, reviewer |
| **Meeting** | Source of decisions/discussions |

### Relationships

| From | Relation | To |
|------|----------|-----|
| PRD | IMPLEMENTED_BY | Blueprint |
| Blueprint | BROKEN_INTO | Work Order |
| Decision | MADE_IN | PRD/Blueprint/Meeting |
| Decision | MADE_BY | Person |
| Work Order | ASSIGNED_TO | Person |
| Meeting | DISCUSSES | Decision |

---

## Data Flow

```
Artifacts (PRD, Blueprint, Work Orders)
         │
         ▼
    ┌─────────┐
    │ Ingest  │  Load and parse JSON/markdown
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ Extract │  LLM extracts decisions, relationships
    └────┬────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌──────────┐
│ Graph │ │Embeddings│
│NetworkX│ │  FAISS   │
└───┬───┘ └────┬─────┘
    │          │
    └────┬─────┘
         ▼
    ┌─────────┐
    │  Query  │  RAG + Graph traversal + LLM synthesis
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │   UI    │  Streamlit
    └─────────┘
```

---

## Core Capabilities

### 1. Context Retrieval

```
User: "Why are we using OAuth instead of SAML?"

→ Vector search finds relevant artifacts
→ Graph traversal finds decision chain
→ LLM synthesizes answer with sources

Response (1.8s):
"Decision made April 15th in Architecture Blueprint.
Mike decided: 'OAuth is simpler for MVP, SAML adds
enterprise complexity we don't need yet.'
Source: blueprint-auth.md, line 42"
```

### 2. Ripple Detection

```
Change: PRD "OAuth 2.0" → "SAML SSO"

→ Find all artifacts referencing OAuth
→ Analyze each for conflicts (parallel LLM)
→ Return affected items with severity

Response (2.3s):
- 1 Blueprint affected (needs rewrite)
- 6 Work Orders invalid
- 2 People to notify: Bob, Alice
```

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Knowledge Graph | NetworkX | In-memory, fast, no setup |
| Vector Store | FAISS | Embedded, simple |
| Embeddings | OpenAI text-embedding-3-small | Fast, good quality |
| LLM | Cerebras | Fast inference (<1s) |
| Frontend | Streamlit | Rapid development |

---

## Performance Targets

| Operation | Target | Why |
|-----------|--------|-----|
| Context query | <3s | Real-time usability |
| Ripple detection | <3s | Prevent mistakes before save |
| Embedding generation | <2s | Fast indexing |

**Why <3 seconds matters:**
- At 2-3s: Usable in workflow
- At 30s: Nobody waits, becomes batch job
- Speed enables prevention, not just reporting

---

## Module Responsibilities

| Module | Purpose |
|--------|---------|
| `ingest.py` | Load PRDs, Blueprints, Work Orders from JSON |
| `graph.py` | Build NetworkX graph with relationships |
| `embeddings.py` | Generate FAISS index for semantic search |
| `query.py` | RAG + graph traversal + LLM synthesis |
| `ripple.py` | Detect downstream impacts of changes |
| `app.py` | Streamlit UI |

---

## Security

- API keys in `.env` (not committed)
- Data stays local (MVP)
- No PII in demo data

---

## Success Metrics

- Answer "Why did we decide X?" in <3s
- Detect ripple effects in <3s
- Demo runs smoothly

---

*Your SDLC shouldn't have amnesia. We fixed that.*
