# AMPM - Demo

---

## The Demo Scenario

### The Setup: ShopFlow Product Team

**Team:** Sarah (PM), Mike (CTO), Bob (Eng Lead), Alice (Design)
**Sprint:** Implementing payment integration

**What exists in AMPM:**
- 4 Meetings: Planning, 2 Standups, Leadership Sync
- 2 Key Decisions: Stripe over Braintree, hosted checkout
- 1 Action Item: Bob to get Legal approval
- 1 Blocker Arc: Legal approval delayed -> escalated -> resolved
- Timeline: May 1-9, 2026

---

## Demo Flow (3 Minutes)

### Opening (15 seconds)

*[Screen shows the AMPM dashboard]*

**SAY:**
> "Let me show you AMPM in action.
>
> We have a typical product team--4 meetings over a week, making decisions, tracking action items.
>
> First, the problem everyone has: understanding WHY things were decided."

---

### Demo 1: Decision Memory (60 seconds)

**SETUP:**
> "Sarah joins the team as a new PM. She sees references to 'the Stripe decision' everywhere. She has no idea what that means or why."

**ACTION:**
Type into the query box:
```
Why did we choose Stripe for payments?
```

*[Press Search, wait for response ~2 seconds]*

**WHILE WAITING:**
> "AMPM is searching across all our meetings, extracting the relevant context..."

**WHEN RESULT APPEARS:**

*[Point to the screen]*

> "1.8 seconds. We have the complete answer.
>
> - The decision was made May 1st in Sprint Planning
> - Mike recommended it, Sarah confirmed
> - The reasoning: 'Better fraud detection, cleaner API, 2 weeks faster integration'
> - There's even the quote from Mike.
>
> Sarah now has full context. No digging through transcripts. No interrupting Mike. No guessing."

**HIGHLIGHT THE TIME:**
> "1.8 seconds. That used to take 30-60 minutes of searching."

---

### Demo 2: Action Item Tracking (60 seconds)

**TRANSITION:**
> "But here's where it gets really powerful.
>
> Action items get lost between meetings. Let's see what happened with Legal approval."

**ACTION:**
Type into the query box:
```
What happened with the Legal approval for payments?
```

*[Wait ~2-3 seconds for response]*

**WHILE WAITING:**
> "AMPM is connecting discussions across multiple meetings..."

**WHEN RESULTS APPEAR:**

*[Point to the timeline]*

> "2.3 seconds. Look at this timeline.
>
> *[Point to each node]*
>
> - May 1st: Bob assigned to get Legal sign-off, estimated 3 days
> - May 4th: Blocker! Legal pushed the meeting to next week
> - May 4th: Sarah escalated to Legal director
> - May 8th: Leadership meeting--Linda approved
> - May 9th: Bob started integration
>
> 8 days total. 5 days blocked on Legal.
>
> And AMPM even extracted the learning: 'Book Legal 2 weeks in advance.'"

**THE PUNCHLINE:**
> "Without AMPM? You piece this together from 4 different meetings.
>
> With AMPM? You see the entire story in 2 seconds. Automatic tracking. Automatic connections."

---

### Demo 3: Meeting History (45 seconds)

**TRANSITION:**
> "Let me show you one more thing."

**ACTION:**
Click on the "Meeting History" tab

**SAY:**
> "Every meeting, automatically analyzed.
>
> *[Point to a meeting]*
>
> Sprint Planning: 2 decisions, 1 action item, 3 topics.
>
> *[Click to expand]*
>
> - Decision 1: Use Stripe for payments
> - Decision 2: Hosted checkout over custom
> - Action: Bob to get Legal sign-off
>
> This is extracted automatically. No manual note-taking. No missing context.
>
> And the Decision Ledger shows every product decision in one place--like a commit history for your product strategy."

---

### Closing (15 seconds)

*[Show the full dashboard one more time]*

**SAY:**
> "AMPM gives your product team a memory.
>
> Every decision remembered. Every action tracked. Every connection made.
>
> From AM to PM, never miss a decision."

*[End]*

---

## Key Lines to Hit

### On Decision Memory:
> "1.8 seconds. That used to take 30-60 minutes."

### On Action Tracking:
> "Without AMPM, you piece this together from 4 different meetings. With it, you see the entire story in 2 seconds."

### On Automatic Extraction:
> "No manual note-taking. No missing context."

### On the Close:
> "From AM to PM, never miss a decision."

---

## Demo Technical Checklist

### Before Demo
- [ ] Streamlit app running (`streamlit run app.py`)
- [ ] Sample data loaded and verified
- [ ] Test both queries work:
  - [ ] "Why did we choose Stripe?" -> Answer in <2s
  - [ ] "What happened with Legal approval?" -> Timeline in <3s
- [ ] Clear any browser cache
- [ ] Close unnecessary apps (prevent slowdowns)
- [ ] Silence notifications

### Backup Plan
- [ ] Have screenshots ready in a folder
- [ ] Know the expected outputs by heart
- [ ] If live demo fails: "Let me show you what this looks like..."

---

## Anticipated Judge Questions

### "How do you extract decisions from transcripts?"

> "We use GPT-4 with specialized prompts. We look for decision patterns--'let's go with,' 'we've decided,' 'the call is.' We confidence-score each extraction and let users correct if needed.
>
> 90%+ accuracy in our testing. The 10% is easy to fix because users review."

### "What if people don't want meetings recorded?"

> "Privacy controls are built-in. Users control what gets captured. You can redact sensitive topics, opt out of specific meetings, or limit who can query.
>
> This is about helping teams, not surveilling them."

### "How is this different from just searching transcripts?"

> "Search gives you 50 results. AMPM gives you an answer.
>
> Search finds mentions. AMPM understands connections--this decision was made because of this context, which led to this action, which hit this blocker.
>
> And search doesn't track action items across meetings. AMPM connects the dots automatically."

### "Why does speed matter?"

> "Real-time enables different workflows.
>
> At 30 seconds per query, you batch questions. You ask at the end of the day.
>
> At 2 seconds, it's part of your flow. You ask in the meeting. You ask while you're coding.
>
> Speed is what makes this usable."

### "What's the business model?"

> "Free tier for small teams. $15/user/month for full features. $40/user for enterprise with compliance.
>
> Gong built a $7B business on sales meetings alone. We're going after all product meetings."

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

## Final Prep Checklist

### Technical
- [ ] App running, data loaded
- [ ] Both demo queries tested
- [ ] Response times verified (<3s)
- [ ] Backup screenshots ready

### Presentation
- [ ] Opening memorized
- [ ] Key lines memorized
- [ ] Transitions smooth
- [ ] Closing strong

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
- End with VISION (from AM to PM)

**The action item timeline is your money shot.** When judges see an 8-day blocker story reconstructed from 4 meetings in 2.3 seconds--that's the "whoa" moment.

**You've got this.**

*From AM to PM, never miss a decision.*
