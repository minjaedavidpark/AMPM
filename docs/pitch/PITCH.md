# AMPM - Pitch Guide
### Everything You Need to Win

---

## The One-Liner (Memorize This)

**"AMPM gives your SDLC a brain. Ask why something exists--get an answer in 2 seconds. Change a requirement--see every downstream impact instantly."**

---

## The 2-Minute Pitch (Full Script)

### Opening: The Story (30 seconds)

*[Start with eye contact, speak slowly]*

> "Let me tell you about something that happened to every engineer in this room.
>
> You pick up a task. It says 'Implement rate limiting on the auth endpoint.'
>
> You think: Why? Why auth specifically? What threshold? What incident caused this?
>
> The ticket doesn't say. The spec just says 'add rate limiting.' The PRD mentions 'security concerns.' Nothing specific.
>
> So you search Slack. 47 results. You ping the PM. They're in meetings. You check the wiki. It's outdated.
>
> An hour later, you still don't have context. So you guess. You build something. You hope it's right.
>
> Two weeks later: 'This doesn't match what we discussed.'
>
> What discussion? That context never reached you."

*[Pause for effect]*

---

### The Problem: Named (15 seconds)

> "This is the SDLC Memory Problem.
>
> As work moves from PRD to Blueprint to Work Order to Code--context dies. Each stage has amnesia about what came before.
>
> Engineers waste 5 to 10 hours per week just searching for 'why.'
>
> Teams build the wrong thing because intent got lost in translation.
>
> Changes upstream don't ripple downstream--until it's too late."

---

### The Solution: AMPM (30 seconds)

> "We built AMPM.
>
> It's a contextual memory layer that sits across your entire SDLC--connecting meetings, PRDs, Blueprints, Work Orders, and Code in a knowledge graph.
>
> Ask 'why does this exist?' Get a complete answer in 2 seconds. With sources.
>
> *[TRANSITION TO DEMO]*
>
> But here's where it gets powerful. Watch what happens when a PM changes a requirement."

---

### The Demo: Ripple Effect (45 seconds)

*[Screen share showing the UI]*

> "The PRD says 'Use OAuth 2.0 for authentication.'
>
> The PM changes it to 'Use SAML SSO.' Enterprise requirement.
>
> *[Make the change in the UI]*
>
> Watch.
>
> *[Ripple effect appears in ~2 seconds]*
>
> In 2.3 seconds, AMPM shows:
>
> - 1 Blueprint affected--needs complete rewrite
> - 6 Work Orders are now invalid
> - 3 code files need to be replaced
>
> It shows exactly WHAT conflicts, WHO to notify, and suggests a migration path.
>
> *[Point to the screen]*
>
> Without this? The team discovers the conflict 3 days later. After building the wrong thing.
>
> With AMPM? They see it in 2 seconds. Before anyone wastes time."

---

### Why Now: The Speed Advantage (15 seconds)

> "This is only possible because we have fast inference.
>
> Analyzing 10 documents for conflicts would normally take 30 seconds. Too slow--nobody waits.
>
> At 2-3 seconds, it's real-time. It happens while you type. It prevents mistakes instead of reporting them.
>
> Speed isn't a feature. Speed is what makes this usable."

---

### The Close: Vision (15 seconds)

> "Modern development is about structured workflows--PRDs to Blueprints to Work Orders to Code.
>
> But a workflow without memory keeps making the same mistakes.
>
> AMPM is the brain that remembers every decision, connects every artifact, and surfaces context at the speed of thought.
>
> Your SDLC shouldn't have amnesia. We fixed that."

*[Pause. Done.]*

---

## Demo Script (Detailed)

### Setup (Before You Start)

**Have these windows ready:**
1. Streamlit app with sample data loaded
2. Terminal showing response times (optional)
3. Sample PRD, Blueprint, Work Orders visible

**Sample Data Scenario:**
- Project: "ShopFlow E-commerce Platform"
- Feature: User Authentication
- PRD mentions OAuth 2.0
- Blueprint implements OAuth with Passport.js
- 6 Work Orders for OAuth tasks
- 3 code files for auth

---

### Demo 1: Context Retrieval (60 seconds)

**Setup the scene:**
> "Imagine you're an engineer. You just joined the team. You're looking at this auth code and wondering: why OAuth? Why not SAML? Let's ask."

**Action:**
Type: `Why are we using OAuth instead of SAML for authentication?`

**While waiting (~2 seconds):**
> "AMPM is searching across meetings, PRDs, Blueprints, Slack discussions, and past decisions..."

**When result appears:**
> "In 1.8 seconds, we have the full context.
>
> - The decision was made April 15th in the Architecture Review meeting
> - Mike, the tech lead, decided it
> - The reasoning: 'OAuth is faster to implement for MVP. SAML adds enterprise complexity we don't need yet.'
> - There's even a link to the meeting where this was debated.
>
> That would have taken 30-60 minutes to find manually. We did it in under 2 seconds."

---

### Demo 2: Ripple Effect (90 seconds)

**Setup the scene:**
> "Now here's the powerful part. Let's say requirements change. An enterprise customer needs SAML. The PM updates the PRD."

**Action:**
1. Navigate to the PRD editor
2. Change "OAuth 2.0" to "SAML SSO"

**As you type:**
> "Watch what happens the moment I make this change..."

**When ripple effect appears:**
> "2.3 seconds. AMPM analyzed every connected artifact and found:
>
> *[Point to each section]*
>
> **One Blueprint affected** - The auth architecture doc references OAuth in four places. All need updating.
>
> **Six Work Orders are now affected** - These tasks were for OAuth. They need to be replaced with SAML tasks.
>
> And it tells us WHO is affected: Bob and Alice, who were assigned to these tasks."

**THE PUNCHLINE:**
> "Without AMPM, the team discovers this conflict on Day 3--after Bob has already built half the OAuth integration.
>
> With AMPM, the PM sees it BEFORE saving the change. We prevent the mistake instead of cleaning up after it."

---

### Demo 3: Meeting to Artifact Tracing (Optional - 45 seconds)

**If time permits:**
> "One more thing. AMPM connects meetings to artifacts.
>
> Let's say I want to know what decisions were made in the Architecture Review meeting.
>
> *[Query the meeting]*
>
> AMPM shows:
>
> - 3 decisions made: OAuth over SAML, Passport.js, Redis sessions
> - Each decision links to the PRD requirement it addresses
> - Each decision links to the Blueprint and Work Orders it created
>
> Full traceability from discussion to implementation."

---

### Closing the Demo

> "That's AMPM.
>
> - Context retrieval: 2 seconds
> - Ripple detection: 2 seconds
> - Meeting to code tracing: Complete
>
> All of this requires fast inference. At normal speeds, these queries take 30+ seconds--too slow to be useful.
>
> At 2-3 seconds, it's real-time. It's in your flow. It actually gets used."

---

## Judge Q&A Preparation

### Q: "How is this different from just using search?"

**Answer:**
> "Search gives you a list of 47 results. AMPM gives you an answer.
>
> Search finds documents. AMPM understands relationships--this decision led to this blueprint, which created these work orders, which produced this code.
>
> And search doesn't detect conflicts. When you change a PRD, Confluence search doesn't tell you which work orders are now invalid. AMPM does, in real-time."

---

### Q: "Why does this need fast inference? Can't you just cache everything?"

**Answer:**
> "You can cache retrieval. You can't cache analysis.
>
> When a PM changes a requirement, we need to analyze 10, 20, maybe 50 documents to find conflicts. That analysis is dynamic--it depends on the specific change.
>
> At 3 seconds per document, that's minutes. Nobody waits.
>
> At 0.3 seconds per document, it's real-time. That's what fast inference enables."

---

### Q: "How do you build the knowledge graph? Is it manual?"

**Answer:**
> "It's automatic. When a meeting happens, we extract decisions. When a PRD is created, AMPM indexes it. When a Blueprint references that PRD, we capture the relationship. When a Work Order implements part of a Blueprint, we link them.
>
> Over time, the graph builds itself from the actual work being done. No manual tagging required.
>
> We also use LLMs to extract implicit relationships--like when someone mentions a decision in a meeting that relates to a PRD."

---

### Q: "What if the graph gets stale?"

**Answer:**
> "That's actually one of the problems we solve. Traditional documentation gets stale because it's static.
>
> AMPM is always connected to the actual artifacts. If a Blueprint is edited, we detect it. If it conflicts with the PRD, we flag it.
>
> Staleness detection is built in. We don't just store information--we monitor for consistency."

---

### Q: "How does this integrate with existing SDLC tools?"

**Answer:**
> "AMPM is designed to work with standard SDLC artifact types.
>
> Each artifact type has a specialized agent that understands its structure--Meeting agent, PRD agent, Blueprint agent, Work Order agent.
>
> They all feed into the central knowledge graph. So when you're looking at a Work Order and want to know why it exists, AMPM can trace it all the way back to the original meeting discussion."

---

### Q: "What if someone disagrees with the AI's analysis?"

**Answer:**
> "AMPM shows its sources. Every answer includes links to the actual artifacts and discussions.
>
> If someone disagrees, they can click through and see the original context. Then they can make their own judgment.
>
> We're not replacing human decisions. We're surfacing context so humans can decide faster and with more information."

---

## Key Messages to Hit

### For the Opening:
- Relatable story (everyone has experienced this)
- Name the problem ("SDLC Memory Problem")
- Quantify the cost (5-10 hours/week)

### For the Solution:
- Simple concept (memory layer for SDLC)
- Concrete capabilities (context retrieval, ripple detection)
- Show, don't tell (demo immediately)

### For the Demo:
- Emphasize SPEED (say the time out loud: "1.8 seconds")
- Show the ripple effect (visual cascade of impacts)
- Make it real (use realistic scenario)

### For the Close:
- Highlight speed advantage (only possible with fast inference)
- Vision statement ("SDLC shouldn't have amnesia")

---

## What NOT to Say

| Don't Say | Say Instead |
|-----------|-------------|
| "We built a knowledge graph" | "We gave your SDLC a memory" |
| "Using AI for analysis" | "Get answers in 2 seconds" |
| "Multi-agent architecture" | "Every artifact has context" |
| "Semantic search" | "Ask in plain English" |
| "Reduces cognitive load" | "Stop wasting hours searching" |

**Lead with the problem and outcome, not the technology.**

---

## Timing Guide

| Section | Time | Cumulative |
|---------|------|------------|
| Opening story | 30s | 0:30 |
| Problem named | 15s | 0:45 |
| Solution intro | 30s | 1:15 |
| Demo: Context | 20s | 1:35 |
| Demo: Ripple | 45s | 2:20 |
| Speed advantage | 15s | 2:35 |
| Close | 15s | 2:50 |
| **Buffer** | 10s | **3:00** |

**Practice to hit 2:50, giving you 10 seconds buffer.**

---

## The Memorable Lines

**Opening hook:**
> "Let me tell you about something that happened to every engineer in this room."

**Problem statement:**
> "Context dies as it moves through the pipeline."

**Speed statement:**
> "2.3 seconds. That analysis. Without fast inference, it takes 30+ seconds--too slow to be useful."

**Demo punchline:**
> "Without AMPM, they discover this on Day 3, after building the wrong thing. With it, they see it before they save."

**Close:**
> "Your SDLC shouldn't have amnesia. We fixed that."

---

## Pre-Pitch Checklist

- [ ] Demo data loaded and tested
- [ ] All three demo queries rehearsed
- [ ] Timing practiced (under 3 minutes)
- [ ] Backup screenshots ready (if live demo fails)
- [ ] Response times verified (<3 seconds)
- [ ] Q&A answers memorized
- [ ] Team roles assigned (who presents, who demos)

---

**Go win this.**
