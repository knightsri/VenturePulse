# MeetingMeter - Meeting Cost Calculator

## Product Vision

A calendar integration that calculates the real cost of every meeting in your organization, surfacing expensive meetings, identifying optimization opportunities, and nudging toward more efficient collaboration.

## Problem Statement

Meetings are the largest hidden expense in most companies:

- Average employee attends 62 meetings per month
- 50% of meeting time is considered unproductive
- A 1-hour meeting with 8 people earning $100K+ costs $400+ in fully-loaded labor
- Companies have no visibility into aggregate meeting spend
- No accountability for meeting efficiency

The pandemic increased meeting frequency by 13%, while making meeting ROI even harder to assess. Companies track every software subscription but ignore the millions spent on internal meetings.

## Target Users

**Primary:** Operations and HR leaders at companies with 100-1,000 employees looking to improve productivity.

**Secondary:** Department heads wanting to understand their team's meeting burden.

**Tertiary:** Individual contributors seeking to protect their time.

## Core Features

### Calendar Integration
- Connect Google Calendar, Outlook, Zoom
- Automatic attendee detection
- Recurring meeting identification
- Cross-calendar visibility (with permissions)

### Cost Calculation
- Import salary bands or use role-based estimates
- Fully-loaded cost calculation (salary + benefits + overhead)
- Per-meeting cost display
- Aggregate views by day/week/month/quarter

### Meeting Analytics Dashboard
- Total meeting spend by team, department, company
- Meeting frequency trends
- Average meeting size and duration
- Top "expensive" meetings ranked
- Time in meetings vs. focused work ratio

### Optimization Insights
- Meetings that could be emails (based on patterns)
- Over-attended meetings (too many people)
- Recurring meetings consuming most budget
- Meeting-free time block analysis
- Comparison to industry benchmarks

### Nudge System
- Pre-meeting cost display when scheduling
- "This meeting costs $X" in calendar event
- Weekly meeting budget reports
- Suggestions to reduce attendees
- Meeting alternatives recommendations

### Team Tools
- Team meeting budgets (soft limits)
- Meeting-free day enforcement
- Async-first suggestions
- Meeting audit capabilities

## Business Model

**SaaS Subscription per Employee:**
- **Team ($4/user/month):** Up to 50 users, core analytics, basic nudges
- **Business ($8/user/month):** Unlimited users, department views, optimization insights
- **Enterprise ($12/user/month):** SSO, API, custom integrations, executive dashboards

**Minimum Contract:** $200/month (protects against tiny teams)

## Technical Architecture

```
┌─────────────────────────────────────────┐
│        Calendar Integrations             │
│  Google Workspace, Microsoft 365, Zoom   │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Data Processing                  │
│  - Event parsing and normalization       │
│  - Attendee resolution                   │
│  - Cost calculation engine               │
│  - Pattern detection                     │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Analytics & Insights             │
│  - Aggregation by org hierarchy          │
│  - Trend analysis                        │
│  - Optimization recommendations          │
│  - Nudge triggers                        │
└─────────────────────────────────────────┘
```

## Market Opportunity

- US companies spend $37B annually on unnecessary meetings
- Productivity software market growing 13% CAGR
- Post-pandemic meeting fatigue creates urgency
- CFO/COO interest in operational efficiency
- Pairs with return-to-office discussions

## Competitive Landscape

| Solution | Gap |
|----------|-----|
| Clockwise | Scheduling optimization, not cost focus |
| Reclaim | AI scheduling, not analytics |
| Calendly | External meetings, not internal |
| Time tracking tools | Manual, not meeting-specific |
| Spreadsheet calculations | One-time, not continuous |

**Our Differentiation:** Pure focus on meeting cost visibility with behavioral nudges—not trying to be a scheduling tool.

## Go-to-Market Strategy

**Phase 1 - Viral Hook:**
- Free meeting cost calculator for individuals
- Chrome extension showing meeting cost
- "Your meetings cost $X this week" shareable reports
- LinkedIn/Twitter content on meeting culture

**Phase 2 - Team Sales:**
- Content marketing for Ops/HR leaders
- ROI calculator showing potential savings
- Case studies with productivity improvements
- Integration with HR platforms

**Phase 3 - Enterprise:**
- Executive dashboards
- Custom organizational hierarchy
- API for integration with BI tools
- Change management playbooks

## Success Metrics

- Users connected (total calendars)
- Meeting spend tracked (total $ calculated)
- Optimization actions taken
- Meeting time reduction over time
- Customer retention and expansion
- NPS (particularly for end users)

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Privacy concerns (salary visibility) | Role-based estimates, aggregated reporting, granular permissions |
| Perceived as "Big Brother" | Individual value prop, opt-in features, positive framing |
| Doesn't change behavior | Focus on nudges and team norms, not just reporting |
| Low willingness to pay for analytics | Tie to concrete savings, free ROI calculation |

## Privacy and Trust Framework

- No individual meeting content access
- Salary data optional (use industry benchmarks)
- Employee consent for individual tracking
- Department-level aggregation by default
- Data deletion on request
- GDPR compliance

## Team Requirements

- 2 full-stack engineers
- 1 data analyst (benchmarks, insights algorithms)
- Founder: product, marketing, sales

## Funding Request

$450K pre-seed for 14-month runway:
- Engineering: $300K
- Data and infrastructure: $50K
- Marketing and content: $60K
- Legal and privacy compliance: $40K

## 14-Month Milestones

- Month 3: MVP with Google Calendar, basic cost calculation
- Month 6: 100 paying teams, $15K MRR, Outlook integration
- Month 10: Optimization insights, nudge system, 250 teams
- Month 14: $50K MRR, first enterprise deals, API launch
