# AMPM - Pitch
---

## The One-Liner (Memorize This)

**"From AM to PM, AMPM is your AI product manager that remembers every decision and tracks every action item--automatically."**

---

## The 2-Minute Pitch (Full Script)

### Opening: The Story (30 seconds)

*[Start with eye contact, speak slowly]*

> "Let me tell you about something that happened to every PM in this room.
>
> You're in a stakeholder meeting. Someone asks: 'Why did we delay internationalization?'
>
> You know the answer is somewhere. Was it Q2 planning? The stakeholder sync? Maybe the CTO mentioned it in that leadership review three weeks ago?
>
> So you start digging. Meeting transcripts. Slack threads. Your own notes--which are incomplete.
>
> An hour later, you still don't have the full picture. So you wing it. You hope you're right.
>
> Next week: 'That's not what we discussed.'"

*[Pause for effect]*

---

### The Problem: Named (15 seconds)

> "This is the Meeting Memory Problem.
>
> Product teams make critical decisions every day. Then those decisions disappear into transcripts nobody reads.
>
> PMs waste 5 to 10 hours per week just searching for 'why.'
>
> New team members take weeks to get context.
>
> And when the PM who made the decision leaves? That knowledge walks out the door."

---

### The Solution: AMPM (30 seconds)

> "We built AMPM--AI Meeting Product Manager.
>
> It's a living memory layer for your product decisions. It extracts decisions, action items, and blockers from every meeting. It connects related discussions across time. It answers 'why did we decide that?' in seconds, with sources.
>
> *[TRANSITION TO DEMO]*
>
> Let me show you."

---

### The Demo: Decision Memory (45 seconds)

*[Screen share showing the UI]*

> "Someone just asked: 'Why are we delaying internationalization?'
>
> *[Type the question, hit search]*
>
> In 2 seconds, AMPM shows:
>
> - The decision was made April 15th in Q2 Planning
> - Sarah, the VP Product, made the call
> - The reasoning: 'Validate US PMF first. I18n is 6 weeks we can't afford.'
> - It was revisited April 22nd when EMEA customers asked
> - It was validated May 20th when US retention hit 15%
>
> *[Point to the screen]*
>
> Full context. Full timeline. Full reasoning.
>
> That used to take an hour of digging. We did it in 2 seconds."

---

### The Second Demo: Action Item Tracking (30 seconds)

> "But here's where it gets really powerful.
>
> 'What happened with Legal approval for payments?'
>
> *[Show the action item timeline]*
>
> AMPM tracked this action item across 5 meetings over 8 days.
>
> - Assigned May 1st, estimated 3 days
> - Blocked May 4th--Legal was unavailable
> - Escalated May 6th--PM got involved
> - Resolved May 8th--Leadership intervened
> - Done May 9th
>
> It even extracted the learning: 'Book Legal 2 weeks in advance.'
>
> This is automatic. We didn't configure anything. AMPM just connected the dots."

---

### The Close: Vision (15 seconds)

> "Product teams make decisions every day. Those decisions shouldn't disappear.
>
> AMPM is the AI product manager that remembers everything--so your team doesn't have to.
>
> From AM to PM, never miss a decision."

*[Pause. Done.]*

---

## Demo Script (Detailed)

### Setup (Before You Start)

**Have these windows ready:**
1. Streamlit app with sample data loaded
2. 4-5 sample meetings in the system
3. Terminal showing response times (optional)

**Sample Data Scenario:**
- Project: ShopFlow E-commerce Platform
- 4 meetings: Planning, 2 Standups, Leadership sync
- Decision: Stripe over Braintree
- Action item: Legal approval (with blocker arc)
- Timeline: May 1-9

---

### Demo 1: Decision Memory (60 seconds)

**Setup the scene:**
> "Imagine you're a new PM. Day one. Someone mentions 'the Stripe decision' and you have no idea what they're talking about. Let's ask AMPM."

**Action:**
Type: `Why did we choose Stripe for payments?`

**While waiting (~2 seconds):**
> "AMPM is searching across all our meetings..."

**When result appears:**
> "1.8 seconds. Full context.
>
> - Sprint Planning, May 1st
> - Mike recommended Stripe over Braintree
> - Reasoning: Better fraud detection, cleaner API, faster integration
> - Sarah confirmed the decision
>
> That would have taken 30-60 minutes to find manually. We did it in under 2 seconds."

---

### Demo 2: Action Item Timeline (60 seconds)

**Setup the scene:**
> "Now let's say you want to know why something took longer than expected. 'What happened with Legal approval?'"

**Action:**
Navigate to the action item tracker, search for "Legal"

**When timeline appears:**
> "AMPM tracked this across 5 meetings automatically.
>
> *[Point to each node]*
>
> - Assigned May 1st in Planning
> - Status check May 2nd--'meeting tomorrow'
> - Blocker May 4th--'Legal pushed to next week'
> - Escalation May 6th--PM stepped in
> - Resolution May 8th--Leadership meeting
> - Done May 9th
>
> 8 days total. 5 days blocked. Root cause: Legal availability.
>
> And the learning AMPM extracted? 'Book Legal 2 weeks in advance.'
>
> No manual tracking. No status spreadsheets. Just automatic connection."

---

### Demo 3: Meeting Health (45 seconds)

**Action:** Show meeting health dashboard

**Say:**
> "One more thing. AMPM also tells you which meetings are valuable.
>
> *[Point to the dashboard]*
>
> Sprint Planning: 9/10. 18 decisions made. High impact.
>
> Standups: 7/10. Good for coordination.
>
> Weekly Product Review: 3/10. Zero decisions in the last month.
>
> AMPM's recommendation? Cancel it. Replace with async updates.
>
> Potential savings: 24 hours per month.
>
> Data-driven meeting management."

---

### Closing the Demo

> "That's AMPM.
>
> - Decision memory: 2 seconds
> - Action item tracking: Automatic
> - Meeting ROI: Data-driven
>
> From AM to PM, never miss a decision."

---

## Judge Q&A Preparation

### Q: "How is this different from Otter.ai?"

**Answer:**
> "Otter transcribes. We analyze.
>
> Otter gives you 50 pages of transcript. AMPM gives you 'This decision was made April 15th by Sarah because X.'
>
> Otter is a recording. AMPM is memory."

---

### Q: "Why product managers specifically?"

**Answer:**
> "PMs feel this pain most acutely. They're in meetings all day, every day. They're asked 'why did we decide that?' multiple times per week.
>
> But this scales to any decision-making team--leadership, engineering, sales. We start narrow to go wide."

---

### Q: "What if people don't want meetings recorded?"

**Answer:**
> "Privacy is built in. Users control what's captured. You can redact sensitive topics. You can opt out of specific meetings.
>
> This is about helping teams, not surveilling them."

---

### Q: "How accurate is the decision extraction?"

**Answer:**
> "LLMs are excellent at intent recognition. We look for decision patterns--'let's go with,' 'we've decided,' 'the call is.'
>
> We confidence-score everything and let users edit. 90%+ accuracy in testing. The 10% is easy to fix."

---

### Q: "What's the business model?"

**Answer:**
> "Free tier for small teams--50 meetings. Team tier at $15/user/month with integrations. Enterprise at $40/user for compliance and API.
>
> Gong built a $7B business on sales meetings alone. We're going after all product meetings."

---

## Key Messages to Hit

### For the Opening:
- Relatable story (everyone has experienced this)
- Name the problem ("Meeting Memory Problem")
- Quantify the cost (5-10 hours/week)

### For the Solution:
- Simple concept (AI PM that remembers)
- Concrete capabilities (decisions, action items, connections)
- Show, don't tell (demo immediately)

### For the Demo:
- Emphasize SPEED (say the time out loud: "1.8 seconds")
- Show the CONNECTIONS (across meetings)
- Make it REAL (use realistic scenario)

### For the Close:
- Strong tagline ("From AM to PM")
- Vision statement ("never miss a decision")
- Call to action

---

## What NOT to Say

| Don't Say | Say Instead |
|-----------|-------------|
| "We built a knowledge graph" | "We gave your meetings a memory" |
| "Using NLP for extraction" | "We extract decisions automatically" |
| "Semantic search capabilities" | "Ask in plain English" |
| "Multi-modal analysis" | "Works with any meeting" |
| "Reduces cognitive load" | "Stop wasting hours searching" |

**Lead with the problem and outcome, not the technology.**

---

## Timing Guide

| Section | Time | Cumulative |
|---------|------|------------|
| Opening story | 30s | 0:30 |
| Problem named | 15s | 0:45 |
| Solution intro | 30s | 1:15 |
| Demo: Decisions | 45s | 2:00 |
| Demo: Actions | 30s | 2:30 |
| Close | 15s | 2:45 |
| **Buffer** | 15s | **3:00** |

**Practice to hit 2:45, giving you 15 seconds buffer.**

---

## The Memorable Lines

**Opening hook:**
> "Let me tell you about something that happened to every PM in this room."

**Problem statement:**
> "Product teams make critical decisions every day. Then they disappear."

**Speed statement:**
> "That used to take an hour. We did it in 2 seconds."

**Demo punchline:**
> "No manual tracking. No status spreadsheets. Just automatic connection."

**Close:**
> "From AM to PM, never miss a decision."

---

## Pre-Pitch Checklist

- [ ] Demo data loaded and tested
- [ ] All demo queries rehearsed
- [ ] Timing practiced (under 3 minutes)
- [ ] Backup screenshots ready (if live demo fails)
- [ ] Response times verified (<3 seconds)
- [ ] Q&A answers memorized
- [ ] Team roles assigned (who presents, who demos)

---

## The AM/PM Hook

**Use this in your opening:**

*"You know what AM and PM means? Morning and afternoon. That's when meetings happen. All. Day. Long.*

*AMPM makes sure the decisions from those meetings don't disappear when they end."*

---

## Why You'll Win

1. **Universal problem** - Every PM, every day
2. **Instant relatability** - Judges have asked "why did we decide that?"
3. **Clear demo** - Question -> answer is obvious value
4. **Smart positioning** - AI PM (not another generic AI tool)
5. **Startup potential** - Obvious path to real business

---

## The Future Vision (If Asked)

### "What's Next for AMPM?"

> "Right now, AMPM analyzes meetings after they happen. But we're building something more ambitious:
>
> **AMPM as a real-time meeting participant.**
>
> Imagine you're in a meeting. Someone asks: 'Why did we delay internationalization again?'
>
> AMPM hears the question, queries the knowledge graph in under 2 seconds, and **responds with audio right there in the meeting**:
>
> *'That decision was made April 15th in Q2 Planning. Sarah decided to validate US product-market fit first because internationalization would take 6 weeks you couldn't afford at the time.'*
>
> No one has to stop the meeting. No one has to dig through notes. AMPM becomes the team's institutional memory—actively participating, not just recording.
>
> That's where we're headed. Post-meeting analysis is Phase 1. Real-time participation is the endgame."

**Technical feasibility:**
- Streaming STT (Deepgram: 100-200ms latency)
- Wake word detection ("Hey AMPM")
- Your existing query engine (<2s)
- TTS response (ElevenLabs: ~500ms)
- **Total: <3 seconds** - fast enough to feel conversational

**Why it matters:**
- Removes friction from knowledge access
- Works during the meeting, not after
- Every meeting becomes smarter because the AI remembers everything

---

**Go win this.**

**From AM to PM, never miss a decision.**
