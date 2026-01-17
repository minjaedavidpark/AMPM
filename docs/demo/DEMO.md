# AMPM - Demo Guide
### The Killer Demo That Wins

---

## The Demo Scenario

### The Setup: ShopFlow E-commerce Platform

**Project:** ShopFlow - an e-commerce platform
**Team:** Sarah (PM), Mike (Tech Lead), Bob & Alice (Engineers)
**Current Sprint:** Implementing user authentication

**What exists in the knowledge graph:**
- 1 PRD: Authentication requirements (OAuth 2.0)
- 1 Blueprint: Auth architecture (Passport.js, Redis sessions)
- 6 Work Orders: OAuth implementation tasks
- 3 Decisions: Why OAuth, why Passport.js, why Redis
- 2 Meetings: Architecture Review, Sprint Planning

---

## Demo Flow (3 Minutes)

### Opening (15 seconds)

*[Screen shows the AMPM dashboard]*

**SAY:**
> "Let me show you AMPM in action.
>
> We have a typical project--ShopFlow. PRD, Blueprint, six Work Orders, all connected.
>
> First, the problem everyone has: understanding WHY things exist."

---

### Demo 1: Context Retrieval (60 seconds)

**SETUP:**
> "Bob just joined the team. He sees a Work Order: 'Implement OAuth callback handler.' He has no idea why OAuth, why not SAML, what the requirements are."

**ACTION:**
Type into the query box:
```
Why are we using OAuth instead of SAML?
```

*[Press Search, wait for response ~2 seconds]*

**WHILE WAITING:**
> "AMPM is searching across PRDs, Blueprints, meetings, Slack discussions..."

**WHEN RESULT APPEARS:**

*[Point to the screen]*

> "1.8 seconds. We have the complete answer.
>
> - The decision was made April 15th in the Architecture Blueprint
> - Mike, the tech lead, decided it
> - The reason: 'Our target customers are startups, not enterprise. OAuth is simpler and faster to implement.'
> - There's even the meeting where they debated this.
>
> Bob now has full context. No searching. No interrupting Mike. No guessing."

**HIGHLIGHT THE TIME:**
> "1.8 seconds. That used to take 30-60 minutes of digging through docs and Slack."

---

### Demo 2: Ripple Detection (90 seconds)

**TRANSITION:**
> "But here's where it gets really powerful.
>
> Requirements change. An enterprise customer needs SAML. The PM updates the PRD."

**ACTION:**
1. Switch to the "Ripple Detection" tab
2. Select "PRD-042" as the artifact
3. Select "OAuth -> SAML" as the change

*[Point to the change description]*

> "We're changing 'OAuth 2.0' to 'SAML SSO.' Seems like a simple text change, right?"

**CLICK:** "Detect Ripple" button

*[Wait ~2-3 seconds for analysis]*

**WHILE WAITING:**
> "AMPM is analyzing every connected artifact for conflicts..."

**WHEN RESULTS APPEAR:**

*[The ripple effect panel shows up with affected items]*

> "2.3 seconds. Look what it found."

*[Point to each section]*

**BLUEPRINTS:**
> "One Blueprint affected. The auth architecture doc references OAuth in four places. All need updating."

**WORK ORDERS:**
> "Six Work Orders are now affected.
>
> - 'Set up Passport OAuth' -- marked INVALID, Passport.js doesn't work for SAML
> - 'Create /auth/google endpoint' -- INVALID, Google is OAuth, not SAML
> - 'Create /auth/github endpoint' -- INVALID, same reason
>
> And it tells us WHO is affected: Bob and Alice, who are assigned to these tasks."

**THE PUNCHLINE:**
> "Without AMPM? The team discovers this on Day 3--after Bob has built half the OAuth integration.
>
> With AMPM? The PM sees it BEFORE saving the change. We prevent the mistake instead of cleaning up after it."

---

### Demo 3: Speed Emphasis (30 seconds)

**SAY:**
> "Let's talk about why this matters.
>
> That analysis looked at 10 artifacts and checked each one for conflicts."

*[Point to the elapsed time]*

> "2.3 seconds total.
>
> Without fast inference, that same analysis takes 30+ seconds. At 30 seconds, nobody waits. It becomes a batch job you run overnight. By then, the mistake is already made.
>
> At 2-3 seconds, it's real-time. It happens while you're typing. It prevents mistakes instead of reporting them.
>
> Speed isn't a nice-to-have. Speed is what makes this usable."

---

### Closing (15 seconds)

*[Show the full dashboard one more time]*

**SAY:**
> "AMPM gives your SDLC a brain.
>
> Every decision remembered. Every artifact connected. Every change analyzed in seconds.
>
> Your SDLC shouldn't have amnesia. We fixed that."

*[End]*

---

## Key Lines to Hit

### On Context Retrieval:
> "1.8 seconds. That used to take 30-60 minutes."

### On Ripple Detection:
> "Without AMPM? They discover this on Day 3, after building the wrong thing. With it? They see it BEFORE saving."

### On Speed:
> "At 30 seconds, nobody waits. At 2-3 seconds, it's real-time. Speed is what makes this usable."

### On the Close:
> "Your SDLC shouldn't have amnesia. We fixed that."

---

## Demo Technical Checklist

### Before Demo
- [ ] Streamlit app running (`streamlit run app.py`)
- [ ] Sample data loaded and verified
- [ ] Test both queries work:
  - [ ] "Why are we using OAuth instead of SAML?" -> Answer in <2s
  - [ ] Ripple detection OAuth->SAML -> Results in <3s
- [ ] Clear any browser cache
- [ ] Close unnecessary apps (prevent slowdowns)
- [ ] Silence notifications

### Backup Plan
- [ ] Have screenshots ready in a folder
- [ ] Know the expected outputs by heart
- [ ] If live demo fails: "Let me show you what this looks like..."

---

## Anticipated Judge Questions

### "How do you build the knowledge graph?"

> "It's automatic. When artifacts are created, AMPM indexes them. When a Blueprint references a PRD, we capture that relationship. When someone discusses a decision in a meeting, we link it to the relevant artifact.
>
> The graph builds itself from the actual work being done."

### "What if the AI makes mistakes?"

> "AMPM always shows its sources. Every answer includes links to the actual artifacts and discussions. If something looks wrong, you can click through and verify.
>
> We're not replacing human judgment. We're surfacing context so humans can decide faster."

### "How is this different from just using search?"

> "Search gives you a list of results. AMPM gives you an answer.
>
> Search finds documents. AMPM understands relationships--this decision was made because of this requirement, which led to these work orders.
>
> And search doesn't detect conflicts. When you change a PRD, Slack search doesn't tell you which work orders are now invalid."

### "Why does this need fast inference?"

> "Real-time requires fast.
>
> When a PM changes a requirement, we analyze multiple documents for conflicts. At 3 seconds per document, that's minutes--nobody waits that long.
>
> At 0.3 seconds per document with fast inference, it's seconds. That's the difference between preventing mistakes and cleaning them up."

### "How does this integrate with existing tools?"

> "AMPM is designed for standard SDLC artifact types. Each artifact type--PRD, Blueprint, Work Order, Code--has a specialized agent that understands its structure.
>
> They all feed into the central knowledge graph. So you get seamless context across the entire pipeline."

---

## Demo Timing

| Section | Duration | Cumulative |
|---------|----------|------------|
| Opening setup | 15s | 0:15 |
| Demo 1: Decision memory | 60s | 1:15 |
| Demo 2: Action tracking | 60s | 2:15 |
| Demo 3: Meeting history | 45s | 3:00 |
| Closing | 15s | 3:15 |
| **Buffer** | - | - |

**Target: 3 minutes flat**

Practice to hit 2:45-3:00, leaving buffer for any delays.

---

## The "Wow" Moments

1. **Decision answer appears** (1.8 seconds)
   - The instant answer with full context
   - "That used to take 30-60 minutes"

2. **Action item timeline** (2.3 seconds)
   - Seeing the full story across meetings
   - "Without AMPM, you piece this together manually"

3. **Automatic extraction**
   - Decisions, actions, blockers--all captured
   - "No manual note-taking"

---

## Optional: Real-Time Vision Demo (If Time Permits)

**Purpose:** Show judges where AMPM is headed - real-time meeting participation

**Setup (Pre-recorded or Live Test):**
1. Have AMPM "join" a mock meeting (screen share)
2. Someone asks: "Hey AMPM, why did we choose Stripe?"
3. Show AMPM responding with audio in <3 seconds
4. Play the TTS response through speakers

**Script:**
> "One more thing I want to show you. This is what we're building next.
>
> *[Switch to real-time demo window]*
>
> AMPM is now joining this meeting as a participant. Watch what happens when someone asks a question during the meeting.
>
> *[Play pre-recorded or have teammate ask live]*
>
> Teammate: 'Hey AMPM, why did we choose Stripe for payments?'
>
> *[AMPM responds with audio in ~2 seconds]*
>
> AMPM: 'Based on the Sprint Planning meeting on May 1st, Mike recommended Stripe over Braintree because of better fraud detection, a cleaner API, and faster integration time—saving about 2 weeks of development.'
>
> *[Pause for effect]*
>
> That just happened in real-time. AMPM heard the question, queried the knowledge graph, and responded—all while the meeting is happening.
>
> This is the future we're building: an AI teammate that remembers every decision and can answer questions the moment they're asked."

**Alternative (If Real-Time Demo Not Ready):**
- Show architecture diagram with real-time flow
- Walk through latency budget (2.2 seconds total)
- Explain technical approach (Deepgram STT, your query engine, ElevenLabs TTS)
- Position as "Phase 2, already architected"

---

## Final Prep Checklist

### Technical
- [ ] App running, data loaded
- [ ] Both demo queries tested
- [ ] Response times verified (<3s)
- [ ] Backup screenshots ready
- [ ] (Optional) Real-time demo tested
- [ ] (Optional) TTS audio working

### Presentation
- [ ] Opening memorized
- [ ] Key lines memorized
- [ ] Transitions smooth
- [ ] Closing strong
- [ ] (Optional) Real-time vision pitch ready

### Team
- [ ] Who presents vs who runs demo
- [ ] Handoff points clear
- [ ] Q&A roles assigned

---

## Remember

**Remember:**
- Lead with the PROBLEM (decisions disappear)
- Show, don't tell (demo immediately)
- Emphasize SPEED (say the times out loud)
- End with VISION (from AM to PM - and future real-time participation)

**The action item timeline is your money shot.** When judges see an 8-day blocker story reconstructed from 4 meetings in 2.3 seconds--that's the "whoa" moment.

**If you show the real-time vision:** That's your closer. The moment judges realize AMPM can answer questions **during** the meeting, not just after—that's when they see the full potential.

**You've got this.**

*From AM to PM, never miss a decision.*
