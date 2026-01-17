# AMPM
### AI Meeting Product Manager
*From AM to PM, Never Miss a Decision*

---

## The 10-Second Pitch

**"Why did we decide that?" shouldn't take 3 hours to answer.**

AMPM is your AI product manager that remembers every decision, tracks every action item, and connects every discussion across all your meetings--automatically.

---

## The Problem

Product teams have meetings all day, every day. Critical decisions happen. Action items are assigned. Context is shared.

**Then it all disappears.**

### The Questions Every PM Asks (And Can't Answer):

**"Why did we deprioritize feature X?"**
-> Somewhere in Q2 planning... or was it the stakeholder sync?

**"Who decided to cut scope on authentication?"**
-> Could be in sprint planning, could be in a 1-on-1, could be in Slack

**"What's blocking the payments team?"**
-> Sarah mentioned something yesterday, but what was it?

**"Have we discussed internationalization before?"**
-> Definitely. Twice? Three times? Who knows.

**"What did the CTO say about our architecture?"**
-> In some meeting 3 weeks ago that you can't find

### The Cost is Brutal:

- **23 hours/month** per person in meetings (Atlassian 2024)
- **40% of that time** wasted due to lack of context (HBR)
- **$37 billion/year** lost to ineffective meetings in US alone
- **Critical knowledge** walks out the door when PMs leave

**Current "solutions" fail:**
- **Meeting transcripts**: 50 pages nobody reads
- **Meeting notes**: Manual, inconsistent, always missing the one thing you need
- **Search**: "Authentication" returns 847 mentions across 200 meetings
- **Memory**: The PM who made the decision quit last month

---

## What is AMPM?

AMPM is an **AI Product Manager** that sits in your meetings and builds a living memory of your product decisions.

It automatically:
1. **Captures** decisions, action items, blockers, and context from every meeting
2. **Connects** related discussions across different meetings and time
3. **Surfaces** exactly what you need, when you need it

### The Core Insight

**Product decisions aren't isolated events--they're connected conversations.**

```
Q2 Planning (Apr 15)
|-- Decision: "Delay internationalization to Q3"
|   |-- Reason: "Focus on US market first, validate PMF"
|   +-- Decided by: VP Product
|
|-- Mentioned in Stakeholder Sync (Apr 22)
|   +-- "EMEA customers asking about localization"
|
|-- Revisited in Sprint Planning (May 6)
|   +-- "Engineering estimates: 6 weeks for i18n"
|
+-- Final Decision in Leadership Review (May 20)
    +-- "Moving i18n to Q3 confirmed, focus on retention"
```

This timeline is **invisible** in traditional tools. AMPM makes it **visible**.

---

## Core Features

### 1. Decision Memory: "Why Did We Decide That?"

**The Killer Feature**

**Input:** "Why are we waiting on internationalization?"

**AMPM Response:**
```
Discussed in 3 meetings:

1. Q2 Planning - April 15, 2026 (Primary Decision)
   Decided by: @sarah (VP Product)

   Key Quote: "We need to validate product-market fit in the
              US before expanding. Internationalization is 6
              weeks of engineering time we can't afford right now."

   Decision: Delay i18n to Q3, focus on US retention

   Related: Product Roadmap, Engineering Capacity

2. Stakeholder Sync - April 22, 2026 (Follow-up)
   Context: "EMEA customers asking about localization. Should
            we reconsider?"

   Decision: Hold firm, explain to customers we're prioritizing
            core features first

3. Leadership Review - May 20, 2026 (Confirmation)
   Validation: "US retention up 15% since April. Right decision
               to focus. Q3 i18n still on track."

   Final: Decision validated, proceeding as planned

Summary: I18n delayed to Q3 to focus on US PMF validation.
         Decision made April 15 by @sarah, validated May 20
         with 15% retention increase.
```

**Impact:**
- New PM gets context in 30 seconds (not 3 hours of digging)
- Stakeholder questions answered with full reasoning
- Historical context prevents re-litigating old decisions

---

### 2. Cross-Meeting Action Item Tracking

**The Problem:** Action items get lost between meetings.

**AMPM Solution:** Automatic tracking across every meeting.

**Example:**

```
Action Item: @bob to validate payment flow with Legal

Timeline:
|-- Assigned: Sprint Planning (May 1)
|   +-- Estimate: 3 days
|
|-- Status Check: Standup (May 2)
|   +-- @bob: "Meeting with Legal tomorrow"
|
|-- Blocker: Standup (May 4)
|   +-- @bob: "Legal pushed meeting to next week"
|
|-- Escalation: PM Sync (May 6)
|   +-- @sarah: "I'll talk to Legal director, this is blocking launch"
|
|-- Resolution: Leadership Meeting (May 8)
|   +-- Legal director: "Approved, sending sign-off today"
|
+-- Completed: Standup (May 9)
    +-- @bob: "Legal approval received, moving forward"

Stats:
|-- Total time: 8 days (estimate was 3 days)
|-- Time blocked: 5 days
|-- Root cause: Legal availability
|-- Resolution: Leadership escalation
+-- Learning: Book Legal reviews 2 weeks in advance
```

**Now you can answer:**
- "What's blocking the payments launch?" (Real-time)
- "Why did Legal approval take 8 days?" (Post-mortem)
- "What's our pattern with Legal blockers?" (Process improvement)

---

### 3. Onboarding in Minutes, Not Weeks

**The Problem:** New PMs miss months of critical context.

**AMPM Solution:** Auto-generated context briefings.

**Example:**

*"I'm the new PM for the Payments team. What should I know?"*

**AMPM Response:**
```
Payments Product Context (Last 6 Months)

Strategic Decisions:
1. Stripe over Braintree (Dec 2025)
   +-- Reason: Better fraud detection, faster integration
   +-- Decided by: @sarah (VP Product)

2. Credit cards only at launch (Jan 2026)
   +-- Reason: Focus on speed to market
   +-- Trade-off: May lose some international customers
   +-- Decided by: Leadership team

3. Subscription billing pushed to Phase 2 (Mar 2026)
   +-- Reason: One-time purchases validate market first
   +-- Decided by: @sarah + @mike (CTO)

Active Initiatives:
|-- Stripe integration (In review, @bob leading)
|-- Fraud detection rules (Blocked on Legal, escalated)
+-- Invoice generation (Planning phase)

Recent Learnings:
|-- Legal reviews take 2 weeks minimum (learned the hard way)
|-- Stripe webhook testing caught 3 critical bugs
+-- Customer support loves the simple checkout flow

Key Stakeholders:
|-- @sarah (VP Product) - Strategic decisions
|-- @bob (Eng Lead) - Technical owner
|-- @alice (Design) - Checkout UX
+-- Linda (Legal) - Compliance reviews

Open Questions:
+-- Do we support PayPal? (Discussed twice, no decision yet)
```

**Impact:**
- Day 1 productivity instead of week 3
- Don't re-ask questions the team already answered
- Understand the "why" behind current priorities

---

### 4. Meeting ROI Dashboard

**The Question:** "Are our meetings valuable?"

**AMPM Tracks:**
- Decisions made per meeting
- Action item completion rate
- Discussion quality (is context being reused?)
- Stakeholder engagement

**Dashboard View:**
```
Meeting Health (Last 30 Days)

Sprint Planning (4 meetings, 8 hrs)
|-- Value Score: 9/10
|-- 18 decisions made
|-- 42 action items (88% completed)
|-- Context referenced in 12 other meetings
+-- ROI: High - Strategic planning time

Standups (20 meetings, 10 hrs)
|-- Value Score: 7/10
|-- 3 decisions (expected for standups)
|-- 47 action items (85% completion)
|-- Avg blocker resolution: 2.3 days
+-- ROI: Good - Coordination working

Stakeholder Updates (4 meetings, 4 hrs)
|-- Value Score: 8/10
|-- 5 decisions made
|-- High engagement from leadership
+-- ROI: Good - Alignment achieved

Weekly Product Review (4 meetings, 4 hrs)
|-- Value Score: 3/10 [WARNING]
|-- 0 decisions made
|-- 2 action items (could be emails)
|-- Never referenced by other meetings
+-- ROI: Low - Consider async updates

Recommendation: Replace Weekly Product Review with
                async written updates + bi-weekly sync

   Potential savings: 4 hours/month x 6 people = 24 hrs
```

**Impact:**
- Data-driven meeting optimization
- Justify canceling low-value meetings
- Optimize for decision-making, not face time

---

### 5. Product Decision Ledger

**Every product decision, documented automatically.**

Think of it as a "commit history" for product strategy.

**Example View:**
```
Product Decision History

May 2026
|-- Delay i18n to Q3 (May 20) - Validated with data
|-- Add Apple Pay support (May 15) - Customer request
+-- Remove guest checkout (May 3) - Security concerns

April 2026
|-- Launch with credit cards only (Apr 28) - Speed to market
|-- Stripe over Braintree (Apr 15) - Better fraud detection
+-- Pricing: $9.99/mo (Apr 8) - Market research

Filters:
|-- By category (Pricing, Features, Technical, Strategic)
|-- By decision maker (@sarah, @mike, Leadership)
|-- By confidence level (High, Medium, Low)
+-- By status (Confirmed, Under Review, Reversed)
```

**Use Cases:**
- Board meeting prep: "What have we decided this quarter?"
- Strategy reviews: "Why did we make these calls?"
- Reversals: "This decision didn't work, what did we miss?"

---

## Tech Stack

### MVP Stack (Hackathon)

| Component | Choice | Why |
|-----------|--------|-----|
| Transcripts | Manual upload (JSON) | No API setup |
| LLM | OpenAI GPT-4 | Fast, reliable |
| Graph | In-memory NetworkX | No DB setup |
| Vector Search | FAISS | Embedded, simple |
| Frontend | Streamlit | Zero frontend code |

### Production Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Transcription** | Whisper API / Meeting APIs | Accurate, multilingual |
| **LLM** | GPT-4 / Claude 3.5 Sonnet | Decision extraction, synthesis |
| **Graph Database** | Neo4j | Native relationship traversal |
| **Vector Database** | ChromaDB | Semantic search |
| **Backend** | Python + FastAPI | Fast, async, ML-friendly |
| **Frontend** | React + TypeScript | Modern, responsive |
| **Visualization** | react-force-graph | Interactive knowledge graph |
| **Integrations** | Zoom, Meet, Teams APIs | Auto-ingest transcripts |

---

## Why This Wins

### 1. Universal Problem
Every product team, every PM, every company has this problem:
- "Why did we decide that?"
- "Who decided to cut that feature?"
- "What's blocking the team?"

### 2. Clear Before/After

**Before AMPM:**
- Decisions buried in transcripts
- Action items lost between meetings
- New PMs lost for weeks
- Re-litigating old decisions
- No visibility into meeting ROI

**After AMPM:**
- Instant decision traceability
- Auto-tracked action items
- Day-1 productivity for new PMs
- Historical context preserved
- Data-driven meeting optimization

### 3. Massive Market

- **$37B/year** wasted on ineffective meetings (US alone)
- **Every company** has meetings (not just tech companies)
- **23 hours/month** per person in meetings = huge TAM
- **Network effects**: More meetings = more valuable

### 4. Clear Comp Landscape

**Gong:** $7.25B valuation (sales meetings only)
**Otter.ai:** $340M raised (transcription, no intelligence)
**Notion:** $10B valuation (knowledge management)

**AMPM's edge:**
- Decision-centric (not just transcription)
- Cross-meeting intelligence (connections over time)
- Product-focused (higher value than general notes)

---

## Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key
- Sample meeting transcripts

### Installation
```bash
# Clone repo
git clone https://github.com/minjaedavidpark/AMPM.git
cd AMPM

# Install dependencies
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY="sk-..."

# Launch dashboard
streamlit run app.py
```

### Example Usage
```bash
# Ask a question
python -c "from src.query import answer_question; print(answer_question('Why did we choose Stripe?'))"

# View decision ledger
streamlit run app.py
```

---

## Sample Meeting Format

```json
{
  "meeting_id": "sprint_planning_2026_05_01",
  "title": "Sprint Planning - May 2026",
  "date": "2026-05-01",
  "duration_minutes": 60,
  "participants": ["Sarah (PM)", "Bob (Eng)", "Alice (Design)", "Mike (CTO)"],
  "transcript": "
    Sarah: Let's discuss the payments launch. Top priority is getting
           Legal approval. Bob, can you take that?

    Bob: Yes, I'll set up a meeting with Linda in Legal this week.

    Mike: How long do we think that'll take?

    Bob: Probably 3 days once we meet.

    Sarah: Great. Make that an action item: Bob to get Legal sign-off
           by end of week. Any blockers we should know about?

    Bob: Not yet, but Legal can be slow. I'll keep you posted.

    Sarah: Perfect. Let's make a decision here: we're going with Stripe's
           hosted checkout instead of building custom. Mike, you good with that?

    Mike: Yeah, makes sense. Faster to market, less maintenance. We can
          always customize later if needed.

    Sarah: Alright, decision made. Stripe hosted checkout it is.
  "
}
```

---

## Why "AMPM"?

**The Name:**
- **AM/PM**: Meetings happen all day, from morning to night
- **AI Meeting Product Manager**: Exactly what it does
- **Memorable**: Easy to say, easy to remember
- **Clever**: The wordplay signals thoughtfulness

**Brand Positioning:**
*"From AM to PM, never miss a decision"*

---

## License

MIT License

---

**AMPM: AI Meeting Product Manager**

*From AM to PM, Never Miss a Decision*

Built to solve a real problem.
Ready to be a real company.
