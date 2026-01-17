# Sample Data

This directory contains sample data for demonstrating AMPM's SDLC memory capabilities.

## SDLC Artifacts (Authentication Feature)

The primary demo scenario showing the PRD → Blueprint → Work Order pipeline:

| File | Artifact Type | Date | Purpose |
|------|---------------|------|---------|
| `prd_authentication_2026_04_10.json` | **PRD** | 2026-04-10 | Authentication requirements, OAuth 2.0 decision |
| `architecture_review_auth_2026_04_12.json` | **Meeting** | 2026-04-12 | OAuth vs SAML decision discussion |
| `blueprint_auth_architecture_2026_04_15.json` | **Blueprint** | 2026-04-15 | Technical architecture, Passport.js decision |
| `workorders_auth_2026_04_20.json` | **Work Orders** | 2026-04-20 | 6 implementation tasks for OAuth |

### Key Decisions (Authentication)

- **OAuth 2.0 over SAML** - Target customers are startups, not enterprise (PRD, Meeting)
- **Passport.js** - De-facto standard for Node.js OAuth (Blueprint)
- **Redis sessions** - Fast read/write, automatic expiration (Blueprint)
- **JWT tokens with 1-hour expiry** - Short-lived for security (Blueprint)

### Ripple Effect Demo

1. Select decision: "Use OAuth 2.0 for authentication instead of SAML"
2. Change to: "Use SAML SSO for enterprise compliance"
3. Ripple shows:
   - 1 Blueprint affected (Passport.js doesn't support SAML)
   - 4+ Work Orders invalidated (WO-001 through WO-004)
   - People to notify: Bob, Diana, Alice

---

## Additional Sample Meetings

| File | Meeting Type | Date | Key Topics |
|------|--------------|------|------------|
| `sprint_planning_2026_05_01.json` | Sprint Planning | 2026-05-01 | Payments, onboarding, mobile strategy |
| `technical_review_2026_04_22.json` | Technical Review | 2026-04-22 | Payment architecture, Stripe vs Braintree |
| `design_review_2026_05_03.json` | Design Review | 2026-05-03 | Checkout flow design |
| `product_roadmap_2026_04_15.json` | Roadmap Planning | 2026-04-15 | Q2 priorities |
| `stakeholder_sync_2026_05_08.json` | Stakeholder Sync | 2026-05-08 | Q2 progress, pricing |
| `engineering_standup_2026_05_06.json` | Daily Standup | 2026-05-06 | Implementation progress |
| `customer_feedback_2026_05_10.json` | Customer Research | 2026-05-10 | Enterprise requirements |
| `incident_postmortem_2026_04_28.json` | Postmortem | 2026-04-28 | April 27 outage |

---

## Sample Queries

### SDLC Context Queries
- "Why are we using OAuth instead of SAML?"
- "Who decided on Passport.js?"
- "What work orders are pending for authentication?"
- "What does the auth blueprint specify?"

### Meeting Context Queries
- "Why did we choose Stripe over Braintree?"
- "What's blocking the payments launch?"
- "What's our mobile strategy?"

---

## Team

| Name | Role |
|------|------|
| Sarah Chen | VP Product |
| Mike Thompson | CTO |
| Bob Martinez | Engineering Lead |
| Alice Kim | Frontend/Design |
| Diana Lee | Backend Engineer |
| Carlos Rivera | Infrastructure |

---

## JSON Schema

```json
{
  "meeting_id": "unique_identifier",
  "title": "Artifact Title",
  "date": "YYYY-MM-DD",
  "duration_minutes": 60,
  "participants": ["Name (Role)", ...],
  "transcript": "Content with DECISION: and ACTION ITEM: markers..."
}
```
