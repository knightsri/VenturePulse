# APIWatch - API Changelog Tracker

## Product Vision

A monitoring service that tracks changes to third-party APIs your applications depend on, alerting you to breaking changes, deprecations, and new features before they impact production.

## Problem Statement

Modern applications depend on dozens of external APIs. When Stripe changes their webhook format, Twilio deprecates an endpoint, or AWS modifies IAM permissions, developers often discover these changes through production incidents.

**Current pain points:**
- Changelog pages are scattered, inconsistent, and easy to miss
- Email announcements get lost in inbox noise
- No unified view of all API dependencies and their status
- Breaking changes discovered during deploys or worse, in production
- Security-relevant changes (auth, permissions) require extra vigilance

## Target Users

**Primary:** Engineering teams at startups and mid-size companies (10-200 engineers) using multiple third-party APIs.

**Secondary:** DevOps/Platform teams responsible for dependency management and upgrade planning.

**Tertiary:** Technical founders who personally manage infrastructure.

## Core Features

### API Catalog
- Add APIs you depend on by name or endpoint URL
- Auto-detection from package.json, requirements.txt, go.mod
- Version pinning and tracking
- Custom internal API support for microservices

### Change Detection Engine
- Monitors official changelog pages, GitHub releases, status pages
- Parses developer blogs and documentation sites
- Detects undocumented changes via API response diffing (opt-in)
- Categorizes changes: breaking, deprecation, new feature, security, performance

### Smart Alerts
- Severity-based notifications (Slack, email, PagerDuty)
- Filter by change type and affected API
- Digest mode (daily/weekly) or real-time for critical changes
- Snooze and acknowledge workflow

### Impact Analysis
- Links detected changes to your codebase (GitHub integration)
- Estimates affected code locations
- Generates upgrade checklist with relevant documentation links
- Migration timeline tracking

### Team Dashboard
- Unified view of all monitored APIs
- Health scores and risk indicators
- Upcoming deprecation timeline
- Audit log of acknowledged changes

## Business Model

**SaaS Subscription:**
- **Free:** 5 APIs, email alerts only, 7-day history
- **Team ($49/month):** 50 APIs, Slack/email/webhook alerts, 90-day history, GitHub integration
- **Business ($199/month):** Unlimited APIs, PagerDuty, SSO, API response diffing, priority support
- **Enterprise:** Custom integrations, dedicated support, SLA

## Technical Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  Change Sources │     │   User Configs   │
│  - Changelogs   │────▶│   - API list     │
│  - GitHub       │     │   - Alert rules  │
│  - Status pages │     │   - Team members │
└─────────────────┘     └──────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│         Change Detection Engine          │
│  - Web scraping + RSS                    │
│  - GitHub API polling                    │
│  - LLM for change classification         │
│  - Response diff analysis                │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Notification & Analysis          │
│  - Severity assessment                   │
│  - Code impact estimation                │
│  - Alert routing                         │
└─────────────────────────────────────────┘
```

## Market Opportunity

- 26M developers worldwide, majority use third-party APIs
- Average application has 20+ external dependencies
- Competing with manual processes (RSS, email, checking docs)
- Adjacent to dependency scanning market ($500M+)

## Competitive Landscape

| Solution | Gap |
|----------|-----|
| Manual changelog checking | Doesn't scale, easy to miss |
| Dependabot/Snyk | Package versions only, not API changes |
| Status pages | Outages only, not deprecations or changes |
| API management platforms | Focus on your APIs, not third-party |
| Postman monitors | Detects breaks, doesn't explain them |

## Go-to-Market Strategy

**Phase 1 - Developer Community:**
- Free tier with generous limits
- Blog posts: "The APIs that broke production this month"
- Open-source changelog aggregator (lead gen)
- Integration with popular dev tools (VS Code extension)

**Phase 2 - Team Sales:**
- Content marketing targeting DevOps personas
- Webinars on API dependency management
- Partner with API providers for co-marketing

**Phase 3 - Enterprise:**
- Security-focused messaging
- SOC2 certification
- Direct sales for 500+ employee companies

## Success Metrics

- APIs monitored (total across all users)
- Alert accuracy (true positive rate)
- Time to detection (vs official announcement)
- User activation (APIs added in first week)
- Team conversion (free → paid)
- NRR (net revenue retention)

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Changelog scraping breaks | Multiple sources per API, fallback to LLM parsing |
| Alert fatigue | Smart batching, severity tuning, easy snooze |
| API providers block scraping | Partnerships, official data source agreements |
| Low perceived value | Focus on "prevented outages" stories, ROI calculator |

## Initial Team

- 1 full-stack engineer (scraping, web app)
- 1 ML engineer (change classification, impact analysis)
- Founder handling product, sales, marketing

## Funding Request

$400K pre-seed for 12-month runway:
- Salaries: $300K
- Infrastructure: $50K
- Legal/compliance: $25K
- Marketing: $25K

## 12-Month Milestones

- Month 3: MVP with 50 pre-configured popular APIs
- Month 6: 1,000 free users, 20 paying teams
- Month 9: GitHub integration, response diffing beta
- Month 12: $15K MRR, 100 paying customers
