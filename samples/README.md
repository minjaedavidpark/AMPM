# Sample Meeting Transcripts

This directory contains mock meeting transcripts for testing and demonstrating AMPM's capabilities.

## Meetings Overview

| File | Meeting Type | Date | Key Topics |
|------|--------------|------|------------|
| `sprint_planning_2026_05_01.json` | Sprint Planning | 2026-05-01 | Payments, onboarding, mobile app strategy |
| `stakeholder_sync_2026_05_08.json` | Stakeholder Sync | 2026-05-08 | Q2 progress, pricing, EMEA expansion |
| `technical_review_2026_04_22.json` | Technical Review | 2026-04-22 | Payment system architecture, Stripe vs Braintree |
| `product_roadmap_2026_04_15.json` | Roadmap Planning | 2026-04-15 | Q2 priorities, feature trade-offs |
| `engineering_standup_2026_05_06.json` | Daily Standup | 2026-05-06 | Implementation progress, blockers |
| `customer_feedback_2026_05_10.json` | Customer Research | 2026-05-10 | Enterprise requirements, feature requests |
| `incident_postmortem_2026_04_28.json` | Postmortem | 2026-04-28 | April 27 outage analysis |
| `design_review_2026_05_03.json` | Design Review | 2026-05-03 | Checkout flow design decisions |

## Key Decisions Across Meetings

### Payment System
- **Stripe over Braintree** - Better developer experience, fraud detection (Technical Review, 04/22)
- **Stripe hosted checkout** - PCI compliance, faster time to market (Sprint Planning, 05/01)
- **Auto-approve refunds under $50** - Reduce friction (Technical Review, 04/22)
- **Annual billing with 20% discount** - Improve cash flow (Stakeholder Sync, 05/08)

### Product Strategy
- **Delay internationalization to Q3** - Focus on US market validation (Roadmap Planning, 04/15)
- **React Native for mobile** - Faster development, team expertise (Sprint Planning, 05/01)
- **Reduce free tier to 10 projects** - Encourage conversion (Roadmap Planning, 04/15)
- **Private beta API for enterprise** - Support key deals (Roadmap Planning, 04/15)

### User Experience
- **Simplified onboarding (8 → 3 fields)** - Reduce time to value (Roadmap Planning, 04/15)
- **Modal checkout flow (Variant C)** - Modern UX, maintains context (Design Review, 05/03)
- **Phone number optional at signup** - Reduce friction (Sprint Planning, 05/01)

### Infrastructure
- **Increase database connection pool to 200** - Handle traffic spikes (Postmortem, 04/28)
- **Marketing notifies engineering 48h before large campaigns** - Process improvement (Postmortem, 04/28)

## Key Action Items

| Assignee | Task | Source Meeting |
|----------|------|----------------|
| Bob | Legal meeting for payments sign-off | Sprint Planning |
| Bob | Mobile technical spec | Sprint Planning |
| Alice | Onboarding mockups | Sprint Planning |
| Carlos | Load testing environment (1000 tpm) | Technical Review |
| Eric | Stripe webhook handlers | Engineering Standup |
| Grace | Professional services proposal | Customer Feedback |
| Tom | Admin control research interviews | Customer Feedback |

## Key Blockers

| Blocker | Status | Resolution |
|---------|--------|------------|
| Legal approval for payments | Resolved | Approved after TOS update |
| Database connection limits | Resolved | Pool increased to 200 |
| Stripe test API keys expired | Resolved | Keys refreshed by Bob |

## Sample Queries to Test

Use these queries to test AMPM's decision tracking:

1. "Why did we choose Stripe over Braintree?"
2. "What's blocking the payments launch?"
3. "Who decided to delay internationalization?"
4. "What changes were made after the April outage?"
5. "What did enterprise customers say about our product?"
6. "Why is the free tier changing?"
7. "What's our mobile strategy?"
8. "When is annual billing launching?"

## JSON Schema

Each meeting follows this structure:

```json
{
  "meeting_id": "unique_identifier",
  "title": "Meeting Title",
  "date": "YYYY-MM-DD",
  "duration_minutes": 60,
  "participants": ["Name (Role)", ...],
  "transcript": "Full meeting transcript..."
}
```

## Usage

```python
from src.ingest import load_meetings

# Load all sample meetings
meetings = load_meetings("samples/")

# Process through AMPM pipeline
for meeting in meetings:
    entities = extract_entities(meeting)
    add_to_graph(entities)
```
