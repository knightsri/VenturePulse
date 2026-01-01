# Section 06: Validation Experiments & Hypotheses

## Objective

Define specific, testable hypotheses and design lean experiments to validate critical assumptions before committing significant resources to building. This section transforms assumptions into actionable experiments with clear success criteria.

---

## Required Elements

### 1. Hypothesis Framework

**Format each hypothesis using the template:**

```
We believe that [target users]
Will [do this action / adopt this behavior]
If we provide [this feature / value / solution]
We will know this is true when we see [measurable outcome]
```

---

**Hypothesis #1: Problem Existence** 🔴 Critical

**Hypothesis Statement:**
We believe that [solo founders and bootstrapped entrepreneurs]
Will [actively seek viability analysis tools]
If they [are trying to validate a new product idea]
We will know this is true when we see [60%+ of surveyed founders confirm this is a top-3 pain point AND 5%+ landing page signup rate]

**Risk Level:** 🔴 Critical (product fails if wrong)

**Current Evidence:**
- Supporting: [Forum discussions, search volume, competitor traction]
- Contradicting: [None identified]
- Gaps: [No direct user interviews yet]

**Experiment Design:**
- **Method:** Customer discovery interviews + landing page test
- **Sample Size:** 20 interviews, 1,000 landing page visitors
- **Duration:** 2 weeks
- **Cost:** $500 (ads) + 20 hours (interviews)

**Success Metrics:**
| Metric | Fail | Minimum | Success | Home Run |
|--------|------|---------|---------|----------|
| Problem confirmation rate | <40% | 40-60% | 60-80% | >80% |
| Landing page signup | <2% | 2-5% | 5-10% | >10% |

**Next Steps if Validated:** Proceed to solution validation
**Next Steps if Invalidated:** Pivot to adjacent problem or exit

---

**Hypothesis #2: Solution Fit** 🔴 Critical

**Hypothesis Statement:**
We believe that [founders seeking validation]
Will [use an AI-powered analysis tool instead of manual research]
If we [deliver comprehensive, actionable reports in minutes instead of weeks]
We will know this is true when we see [70%+ of prototype users rate the output as "useful" or "very useful"]

**Risk Level:** 🔴 Critical

*[Continue with same format...]*

---

**Hypothesis #3: Willingness to Pay** 🔴 Critical

**Hypothesis Statement:**
We believe that [bootstrapped founders]
Will [pay $49-$99 for a single viability analysis]
If we [provide investor-grade output that saves 20+ hours of research]
We will know this is true when we see [10+ pre-orders at target price point]

*[Continue with same format...]*

---

**(Continue for 8-12 total hypotheses covering):**
- Problem hypotheses (2-3)
- Solution hypotheses (2-3)
- Pricing hypotheses (2-3)
- Channel hypotheses (2-3)

---

### 2. Experiment Catalog

**Design 10-15 experiments to test hypotheses:**

---

**Experiment #1: Problem Discovery Interviews**

**Hypothesis Tested:** #1 (Problem Existence)

**Method:** Semi-structured interviews with target users

**Setup:**
1. Recruit 20-30 founders via LinkedIn, Twitter, Reddit
2. Offer $50 gift card incentive
3. Schedule 45-60 minute video calls
4. Use interview guide (see User Research section)
5. Record and transcribe conversations

**Metrics:**
- % confirming problem as top-3 pain
- Frequency of problem occurrence
- Current spend on alternatives (time/money)
- Quotes indicating severity

**Timeline:** 2 weeks (parallel recruitment and interviews)

**Cost:** $1,000-$1,500 (incentives)

**Success Criteria:**
- ✅ Pass: 60%+ confirm problem as significant
- ⚠️ Re-evaluate: 40-60% confirmation
- ❌ Fail: <40% confirmation

**Owner:** [Assign responsibility]

---

**Experiment #2: Landing Page Smoke Test**

**Hypothesis Tested:** #1 (Problem Existence) + #2 (Solution Interest)

**Method:** Landing page with waitlist signup

**Setup:**
1. Create single landing page (Carrd, Unbounce, or custom)
2. Write compelling headline and value proposition
3. Add waitlist email capture form
4. Drive traffic via Google/Facebook ads
5. Track conversions with analytics

**Variants to Test:**
- Headline A: "Validate your startup idea in 24 hours"
- Headline B: "AI replaces your $50K business consultant"
- Headline C: "Stop building products nobody wants"

**Metrics:**
- Traffic volume (target: 1,000+ visitors)
- Signup rate by variant
- Time on page
- Scroll depth

**Timeline:** 2 weeks (1 week setup, 1 week traffic)

**Cost:** $500-$1,000 (ads)

**Success Criteria:**
- ✅ Pass: >5% signup rate
- ⚠️ Re-evaluate: 2-5% signup rate
- ❌ Fail: <2% signup rate

---

**Experiment #3: Wizard of Oz MVP**

**Hypothesis Tested:** #2 (Solution Fit) + #3 (Willingness to Pay)

**Method:** Manually deliver the service using AI + human judgment

**Setup:**
1. Accept project specs via Google Form
2. Generate analysis using Claude/GPT with custom prompts
3. Polish and format output manually
4. Deliver via email with feedback request
5. Offer to pay after receiving output

**Metrics:**
- Time to deliver (target: <24 hours)
- User satisfaction (1-10 rating)
- NPS score
- % willing to pay after seeing output
- Actual payment conversion

**Timeline:** 4 weeks (10-20 users)

**Cost:** Time only (10-20 hours of effort)

**Success Criteria:**
- ✅ Pass: 8+/10 avg satisfaction, 50%+ would pay
- ⚠️ Re-evaluate: 6-8/10 satisfaction
- ❌ Fail: <6/10 satisfaction, <30% would pay

---

**(Continue for 7-12 more experiments):**

**Experiment #4: Pricing Survey (Van Westendorp)**
- Test price sensitivity and optimal price point

**Experiment #5: Competitor Tear-Down Interviews**
- Understand why users chose alternatives

**Experiment #6: Pre-Order Test**
- Collect actual payments before building

**Experiment #7: Fake Door Feature Test**
- Measure interest in specific features

**Experiment #8: Channel Testing**
- Test CAC across Google, Facebook, LinkedIn, Reddit

**Experiment #9: Referral Mechanism Test**
- Test viral coefficient with early users

**Experiment #10: Retention Experiment**
- Measure if users return for second analysis

---

### 3. Experiment Prioritization Matrix

**Prioritize experiments by impact and effort:**

| Experiment | Hypothesis | Impact | Effort | Risk if Skipped | Priority |
|------------|------------|--------|--------|-----------------|----------|
| Discovery Interviews | #1 | 🔴 Critical | Medium | Fail | 1 |
| Landing Page Test | #1, #2 | 🔴 Critical | Low | Fail | 2 |
| Wizard of Oz MVP | #2, #3 | 🔴 Critical | High | Fail | 3 |
| Pricing Survey | #3 | 🟡 High | Low | Suboptimal pricing | 4 |
| Pre-Order Test | #3 | 🟢 Medium | Medium | Lack of validation | 5 |
| Channel Testing | #4 | 🟢 Medium | Medium | Inefficient CAC | 6 |

**Priority Logic:**
1. **Critical Path First:** Experiments that determine Go/No-Go
2. **Low Effort, High Impact:** Quick wins for validation
3. **Dependent Experiments Last:** Only run after prerequisites pass

---

### 4. Experiment Schedule (8-Week Sprint)

**Week 1-2: Problem Validation**
| Day | Activity | Owner | Deliverable |
|-----|----------|-------|-------------|
| D1-D3 | Launch landing page | | Live page + analytics |
| D1-D7 | Recruit interview participants | | 20 scheduled calls |
| D4-D14 | Conduct interviews | | 20 completed, transcribed |
| D8-D14 | Run landing page ads ($500) | | 1,000+ visitors |

**Week 3-4: Solution Validation**
| Day | Activity | Owner | Deliverable |
|-----|----------|-------|-------------|
| D15-D18 | Analyze interview data | | Problem validation report |
| D15-D21 | Build Wizard of Oz process | | Manual delivery workflow |
| D19-D28 | Deliver to 10 users | | 10 completed analyses |

**Week 5-6: Pricing & Willingness to Pay**
| Day | Activity | Owner | Deliverable |
|-----|----------|-------|-------------|
| D29-D35 | Run pricing survey | | 100+ responses |
| D29-D35 | Collect post-delivery payments | | Payment conversion data |
| D36-D42 | Analyze pricing data | | Optimal price recommendation |

**Week 7-8: Synthesis & Decision**
| Day | Activity | Owner | Deliverable |
|-----|----------|-------|-------------|
| D43-D49 | Compile all experiment results | | Validation summary |
| D50-D52 | Make Go/No-Go decision | | Decision document |
| D53-D56 | Plan Phase 2 (if Go) | | MVP spec or pivot plan |

---

### 5. Minimum Success Criteria (Go/No-Go)

**Define the minimum bar for proceeding:**

| Category | Metric | Must Achieve | Nice-to-Have |
|----------|--------|--------------|--------------|
| **Problem** | Interview confirmation | 60%+ | 80%+ |
| **Problem** | Landing page signup | 5%+ | 10%+ |
| **Solution** | Prototype satisfaction | 7/10+ | 8.5/10+ |
| **Solution** | NPS | 30+ | 50+ |
| **Pricing** | Willingness to pay at $X | 50%+ | 70%+ |
| **Pricing** | Pre-orders collected | 10+ | 25+ |
| **Overall** | Hypotheses validated | 3/5 critical | 5/5 critical |

**Go Decision:** All "Must Achieve" criteria met
**Conditional Go:** 70% of criteria met, clear path to remainder
**No-Go Decision:** <70% of criteria met, no clear fixes

---

### 6. Pivot Triggers & Contingency Plans

**Define when to pivot and what to do:**

**Trigger #1: Problem Doesn't Exist**
- **Signal:** <40% of users confirm problem
- **Action:** Interview users about their actual top problems, identify adjacent pain points
- **Pivot Options:** Different problem in same audience, same problem in different audience

**Trigger #2: Solution Doesn't Resonate**
- **Signal:** <50% satisfaction with prototype
- **Action:** Deep-dive on what's missing, what's confusing, what's not valuable
- **Pivot Options:** Simplify scope, change format, add human touch

**Trigger #3: Won't Pay Enough**
- **Signal:** Acceptable price is <50% of target
- **Action:** Find higher-value use case, different segment, or reduce costs
- **Pivot Options:** Freemium with upsell, enterprise pivot, cost optimization

**Trigger #4: Can't Acquire Efficiently**
- **Signal:** CAC >3x target in all channel tests
- **Action:** Test organic/viral channels, reconsider pricing model
- **Pivot Options:** Product-led growth, community-first, partnership distribution

---

### 7. Experiment Documentation Template

**For each completed experiment, document:**

```markdown
## Experiment: [Name]
**Date:** [Start - End]
**Hypothesis Tested:** #X

### Setup
- What we did
- Sample size
- Tools used
- Cost incurred

### Results
| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|

### Key Learnings
- Insight #1
- Insight #2
- Surprise finding

### Evidence
- [Link to data]
- [Quotes/screenshots]

### Next Steps
- [What this means for the product]
- [Follow-up experiments needed]
```

---

## Output Requirements

### HTML Structure:
```html
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
    <h2>Validation Experiments & Hypotheses</h2>
    
    <!-- Hypothesis Cards -->
    <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 1rem; margin: 1rem 0;">
        <h4>Hypothesis #1: Problem Existence 🔴 Critical</h4>
        <p><strong>We believe that...</strong></p>
        <!-- Full hypothesis -->
    </div>
    
    <!-- Experiment Table -->
    <h3>Experiment Catalog</h3>
    <table><!-- Experiments --></table>
    
    <!-- Timeline Gantt -->
    <h3>8-Week Validation Sprint</h3>
    <!-- Visual timeline -->
    
    <!-- Go/No-Go Criteria -->
</div>
```

### Length Target:
- **Total:** 1200-1600 words
- **Focus areas:**
  - Hypotheses: 30%
  - Experiment designs: 35%
  - Schedule & prioritization: 20%
  - Go/No-Go & pivots: 15%

---

## Final Checklist

Before submitting, verify:
- [ ] 8-12 hypotheses written in structured format
- [ ] Each hypothesis has risk level, evidence, and success metrics
- [ ] 10-15 experiments designed with clear methods
- [ ] Each experiment has cost, timeline, and success criteria
- [ ] Experiment prioritization matrix included
- [ ] 8-week validation schedule with weekly activities
- [ ] Minimum success criteria for Go/No-Go defined
- [ ] Pivot triggers and contingency plans documented
- [ ] Experiment documentation template provided
- [ ] HTML is complete and styled
- [ ] Experiments are practical and actionable
- [ ] Self-contained (no external dependencies)

---

**Generate the Validation Experiments section now using the project data provided.**
