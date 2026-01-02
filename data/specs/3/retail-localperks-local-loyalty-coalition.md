# LocalPerks - Local Loyalty Coalition

## Product Vision

A shared loyalty program that lets independent local businesses band together to offer rewards that rival big chains—earn points at the coffee shop, redeem at the bookstore, building a local commerce ecosystem.

## Problem Statement

Independent local businesses can't compete with chain loyalty programs:

- Starbucks Rewards has 31M active members
- Small coffee shop can't afford to build an app or manage a points program
- Individual punch cards are fragmented and forgotten
- Consumers default to chains because rewards add up faster
- Local spending doesn't accumulate into meaningful benefits

Meanwhile, consumers want to support local but chain rewards create friction to switching.

## Target Users

**Primary:** Independent retail businesses in walkable commercial districts: coffee shops, bookstores, restaurants, boutiques.

**Secondary:** Consumers who value local businesses but appreciate rewards and convenience.

**Tertiary:** Local business associations, downtown development organizations, and local chambers of commerce.

## Core Features

### For Businesses

**Easy Enrollment:**
- Sign up in 10 minutes
- No hardware required (tablet POS or phone)
- Set your own earn/redeem rates
- Choose which coalition networks to join

**Simple Operations:**
- Customer scans QR code or gives phone number
- Points awarded automatically
- Real-time dashboard showing redemptions
- Settlement handled monthly

**Marketing Tools:**
- Access to coalition email list (opt-in)
- Joint promotions with neighbor businesses
- Spotlight features in consumer app
- New customer acquisition tracking

### For Consumers

**Unified Wallet:**
- One app, one balance across all local businesses
- Points earned everywhere in coalition
- Clear earn rates and redemption options
- Transaction history and receipts

**Discovery Features:**
- Map of participating local businesses
- "Near me" with earn rates
- New business notifications
- Categories and favorites

**Rewards Flexibility:**
- Redeem at any participating business
- Tiered rewards (more points = better perks)
- Special member-only offers
- Birthday and milestone bonuses

### For Coalitions

**Network Management:**
- Business association dashboard
- Member recruitment tools
- Joint marketing campaigns
- Economic impact reporting

## Business Model

**Business Subscription:**
- **Basic ($29/month):** Participate in coalition, basic features
- **Pro ($59/month):** Marketing tools, analytics, featured placement
- **Enterprise (custom):** Multi-location, API access

**Transaction Fees:**
- No fee for earning points
- 5% fee on redemptions (charged to redeeming business)
- Covers interchange and processing

**Coalition Fees:**
- Business association license: $199/month for up to 50 businesses
- Includes marketing support and dedicated success manager

## Technical Architecture

```
┌─────────────────────────────────────────┐
│        Consumer Mobile App               │
│  - React Native (iOS/Android)            │
│  - QR scanning                           │
│  - Wallet and history                    │
│  - Local business discovery              │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Backend Platform                 │
│  - Points ledger                         │
│  - Business management                   │
│  - Coalition networking                  │
│  - Settlement engine                     │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│        Business Dashboard                │
│  - Web-based                             │
│  - Transaction processing                │
│  - Customer insights                     │
│  - Marketing tools                       │
└─────────────────────────────────────────┘
```

## Market Opportunity

- 30.7M small businesses in US
- Local retail represents $4T in annual spending
- 79% of consumers want to support local businesses
- Loyalty program market: $5.5B and growing
- Buy-local movements gaining momentum

## Competitive Analysis

| Solution | Gap |
|----------|-----|
| Individual punch cards | Fragmented, forgettable |
| Toast/Square loyalty | Single-business, not coalition |
| Belly (defunct) | Proved concept but failed on execution |
| Fivestars | SMB focus but not coalition model |
| Chain programs | Not available to independents |

**Our Differentiation:** Coalition model creates network effects—more businesses = more consumer value = more businesses.

## Go-to-Market Strategy

**Phase 1 - Pilot Neighborhoods:**
- Partner with 3-5 downtown business associations
- Goal: 20-30 businesses per neighborhood
- Consumer launch with coalition marketing
- Refine based on feedback

**Phase 2 - City Expansion:**
- Playbook for new neighborhood launch
- Business association sales motion
- Consumer growth through neighborhood density
- Regional marketing

**Phase 3 - Multi-City:**
- Franchise-like model for new cities
- National consumer app presence
- Travel/visiting feature (find local perks anywhere)

## Success Metrics

- Businesses enrolled per neighborhood
- Consumer app downloads and active users
- Points earned and redeemed
- Cross-business redemption rate (key coalition metric)
- Business retention
- Consumer visit frequency change

## Coalition Economics

**For a 30-business coalition:**
- Average transaction: $25
- Points earned: 5% ($1.25)
- Redemption rate: 60% of points
- Cross-business redemption: 40%

**Business Value:**
- Access to customers from 29 other businesses
- Average cost per redemption: 5% of transaction
- ROI through new customer acquisition

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Chicken-and-egg (consumers need businesses, vice versa) | Launch in tight neighborhood clusters, achieve density |
| Free-rider businesses (benefit without contributing) | Minimum participation requirements, gamification |
| Consumer adoption friction | Aggressive launch incentives, simple phone number signup |
| Settlement complexity | Conservative floats, clear terms, automated monthly |
| Business churn | Lock-in through consumer relationships, coalition community |

## Regulatory Considerations

- Stored value regulations vary by state
- Money transmitter licensing may be required
- Gift card laws apply to points
- Privacy regulations for consumer data

Plan for legal review before launch and state-by-state compliance strategy.

## Team Requirements

- 2 full-stack engineers (web + mobile)
- 1 community manager (business and coalition relationships)
- Founder: product, sales, partnerships

## Funding Request

$500K seed for 14-month runway:
- Engineering: $300K
- Community and business development: $100K
- Marketing (launch campaigns): $60K
- Legal and compliance: $40K

## 14-Month Milestones

- Month 4: MVP with 2 pilot neighborhoods, 40 businesses
- Month 7: Consumer app launch, 5,000 downloads
- Month 10: 5 neighborhoods, 100 businesses, $30K MRR
- Month 14: 10 neighborhoods, 3 cities, $75K MRR, playbook proven
