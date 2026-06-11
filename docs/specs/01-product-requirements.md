# CarbonSense AI — Product Requirements Document

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Deadline:** Sun, Jun 21, 2026 11:59 PM IST  
**Author:** Sovan Bhakta

---

## 1. Product Overview

### 1.1 Vision

CarbonSense AI turns carbon awareness into a continuous coaching journey — making sustainable living achievable through personalized AI intelligence, not generic advice.

### 1.2 Problem

Most carbon footprint tools follow a dead-end pattern:

```
User enters data → Carbon calculated → Generic report → User leaves
```

Three fundamental failures:

| Problem | Impact |
|---------|--------|
| No contextual intelligence | Every user gets identical generic advice regardless of lifestyle |
| No continuity | Each session starts from scratch — no memory of prior behavior |
| No behavioral engagement | Static numbers don't motivate action or drive sustainable change |

### 1.3 Solution

CarbonSense AI is a full-stack multi-agent sustainability coaching platform. Instead of stopping at calculation, it coaches. A 4-agent AI pipeline (Baseline → Analyst → Planner → Coach) analyzes lifestyle patterns, generates adaptive reduction plans, and coaches users toward measurable goals — all powered by Google Gemini 1.5 Flash.

### 1.4 Differentiator

A standard tool says: *"Your monthly footprint is 215 kg CO₂."*

CarbonSense AI says: *"Transportation contributes 52% of your footprint. By replacing 2 weekly car trips with public transport, you could reduce emissions by 18 kg/month. Want me to create a 30-day reduction plan?"*

Then two weeks later: *"You've reduced transport emissions by 8%. Let's increase your goal from 10% to 15%."*

This is the difference between a calculator and a coach.

---

## 2. User Personas

### 2.1 Persona A — Climate-Conscious Individual (Primary)

| Attribute | Detail |
|-----------|--------|
| **Demographics** | Age 20–40, urban or suburban, India-based |
| **Motivation** | Personally motivated to reduce environmental impact |
| **Pain Points** | Existing tools are generic and complex; advice not actionable; no way to track real progress |
| **Behaviors** | Willing to log activities daily if feedback is meaningful and personalized |
| **Goal** | Reduce personal carbon footprint by a specific, measurable percentage |

### 2.2 Persona B — Sustainability-Curious Learner (Secondary)

| Attribute | Detail |
|-----------|--------|
| **Demographics** | Age 18–35, new to carbon tracking |
| **Motivation** | Exploring sustainable living, curious about personal impact |
| **Pain Points** | Doesn't know where to start; overwhelmed by data; needs education alongside action |
| **Behaviors** | Responds well to gamification, milestones, and visible progress indicators |
| **Goal** | Understand environmental impact and take first steps toward change |

---

## 3. Core Feature List

| # | Feature | Priority | Description |
|---|---------|----------|-------------|
| F1 | AI Sustainability Coach | P0 | Streaming chat interface powered by Gemini 1.5 Flash; orchestrates between user and agent pipeline |
| F2 | User Onboarding & Baseline Agent | P0 | 4-step wizard collecting profile data; Baseline Agent calculates initial footprint estimate |
| F3 | Activity Logger | P0 | Dual-input system (structured form + natural language via Gemini function calling) for logging activities |
| F4 | Carbon Engine | P0 | Deterministic, AI-free calculation layer using IPCC/EPA/peer-reviewed emission factors |
| F5 | Multi-Agent Intelligence Layer | P0 | Custom sequential pipeline: Analyst → Planner → Coach with typed Pydantic inter-agent communication |
| F6 | Insights Dashboard | P0 | Recharts-based analytics panel: monthly footprint, category breakdown, trend chart, goal progress, Eco Points |
| F7 | Mission Center | P1 | Gamified challenges from Planner Agent recommendations; Eco Points rewards with tier system |

---

## 4. Functional Requirements

### F1 — AI Sustainability Coach

| ID | Requirement |
|----|-------------|
| FR-1.1 | Accept free-form natural language input from the user |
| FR-1.2 | Stream responses token-by-token via SSE (`text/event-stream`) for real-time feedback |
| FR-1.3 | Maintain conversation history within a session (last 10 turns retained in context) |
| FR-1.4 | Trigger the full agent pipeline (Analyst → Planner → Coach) on explicit analysis requests |
| FR-1.5 | Parse natural language activity descriptions into structured entries via Gemini function calling |
| FR-1.6 | Surface agent pipeline results through Coach Agent's conversational output |

### F2 — User Onboarding & Baseline Agent

| ID | Requirement |
|----|-------------|
| FR-2.1 | Collect user profile: name, country, city, lifestyle type (urban / suburban / rural) |
| FR-2.2 | Collect transport habits: primary mode, estimated weekly distance (km) |
| FR-2.3 | Collect food habits: diet type (vegan / vegetarian / mixed / high_meat) |
| FR-2.4 | Collect energy usage: monthly electricity kWh, heating type (LPG / electric / none) |
| FR-2.5 | Generate session UUID (stored in `localStorage` — no authentication for MVP) |
| FR-2.6 | Baseline Agent analyzes profile via Gemini function calling → initial footprint estimate per category |
| FR-2.7 | Store baseline as permanent reference for all future progress calculations |
| FR-2.8 | Skip onboarding if valid user UUID exists in `localStorage` |

### F3 — Activity Logger

| ID | Requirement |
|----|-------------|
| FR-3.1 | Structured form input for all 4 categories (transport, energy, food, shopping) with unit selection |
| FR-3.2 | Natural language input auto-parsed to structured JSON via Gemini function calling |
| FR-3.3 | Carbon kg CO₂ calculated by Carbon Engine immediately on save |
| FR-3.4 | Activity history view: paginated, filterable by category and date range |
| FR-3.5 | Delete activity entries with carbon total recalculation |
| FR-3.6 | New activity log invalidates 24-hour insight cache |

### F4 — Carbon Engine

| ID | Requirement |
|----|-------------|
| FR-4.1 | Calculate kg CO₂ for any activity given: category, type, amount |
| FR-4.2 | Aggregate monthly footprint totals broken down by category |
| FR-4.3 | Calculate percentage share of each category in total footprint |
| FR-4.4 | Generate historical trend data for 7-day, 30-day, 90-day windows |
| FR-4.5 | Track progress as percentage reduction from baseline footprint |
| FR-4.6 | Compare user footprint against India national average (1.9 tonnes CO₂/year ≈ 158 kg/month) |
| FR-4.7 | All emission factors documented with source citations in code comments |

### F5 — Multi-Agent Intelligence Layer

| ID | Requirement |
|----|-------------|
| FR-5.1 | Agents communicate exclusively via validated Pydantic models — no free-text inter-agent communication |
| FR-5.2 | Each agent receives only required context (minimal context principle) |
| FR-5.3 | Full pipeline triggered within single `POST /api/v1/agents/analyze` call |
| FR-5.4 | Agent outputs cached 24 hours per user; invalidated on new activity log |
| FR-5.5 | Coach Agent response streamed to frontend via SSE |
| FR-5.6 | Pipeline validates each stage output against Pydantic schema before passing to next agent |
| FR-5.7 | Rate limit: 3 full pipeline runs per user per hour |

### F6 — Insights Dashboard

| ID | Requirement |
|----|-------------|
| FR-6.1 | Dashboard loads with latest aggregated data on every visit (client-side fetch on mount) |
| FR-6.2 | Time range selector for Historical Trend chart (7 / 30 / 90 days) |
| FR-6.3 | All charts include hover tooltips with exact values |
| FR-6.4 | Empty state for new users with prompt to log first activity |
| FR-6.5 | All charts have ARIA labels and are keyboard-navigable |

### F7 — Mission Center

| ID | Requirement |
|----|-------------|
| FR-7.1 | Planner Agent generates 2–3 mission suggestions based on top emission categories |
| FR-7.2 | User can accept or dismiss each mission suggestion |
| FR-7.3 | Accepted missions have a deadline; auto-expire if not completed |
| FR-7.4 | Mission completion records activity entry that reduces measured footprint |
| FR-7.5 | Eco Points awarded and balance updated immediately on completion |
| FR-7.6 | Eco Points balance and tier (Seedling / Sapling / Tree / Forest) visible in nav header |
| FR-7.7 | Active missions displayed with progress indicators and days remaining |

---

## 5. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | FCP ≤ 2s (Vercel CDN). API P95 latency ≤ 500ms (non-AI endpoints). AI first token streamed ≤ 2s. Full agent pipeline completes ≤ 10s. Dashboard queries < 50ms. |
| **Security** | `GEMINI_API_KEY` in `.env` only, never committed. CORS configured to `ALLOWED_ORIGINS` allowlist (never `*` in production). AI endpoints rate-limited per user. All request bodies validated with Pydantic v2. No sensitive data in `localStorage` beyond UUID. |
| **Reliability** | Backend on Render with 14-minute frontend keepalive ping to `/api/v1/health`. Frontend on Vercel (99.9% SLA). Graceful error handling on Gemini API failures — never raw exceptions to frontend. |
| **Accessibility** | WCAG 2.1 AA compliance. Full keyboard navigation. ARIA labels on all interactive elements and data visualizations. Minimum color contrast ratio 4.5:1. Focus management on route changes. |
| **Browser Support** | Chrome 120+, Firefox 120+, Safari 17+, Edge 120+. |
| **Repository** | Single branch (`main`). Total size ≤ 10 MB. Public GitHub repository. `README.md` documents vertical chosen, approach, how solution works, assumptions made. |
| **Testability** | ≥ 90% coverage on Carbon Engine. ≥ 80% on API routes. ≥ 70% on agent orchestrator (mocked Gemini). ≥ 60% on frontend components. |

---

## 6. Constraints and Assumptions

### 6.1 Constraints

| Constraint | Source | Impact |
|-----------|--------|--------|
| Single branch (`main`) | Competition rules | No feature branches; CI runs on push to main |
| Repository < 10 MB | Competition rules | No large assets; `node_modules` and `__pycache__` in `.gitignore` |
| Public repo | Competition rules | No proprietary code; API keys must be in `.env` |
| 3 max submission attempts | Competition rules | Each overwrites previous score; submit strategically |
| Score multiplier decays over time | Competition rules | Earlier submission = higher final score |
| Render free tier | Infrastructure | 512 MB RAM, ephemeral disk on redeploy, spins down after 15 min inactivity |
| SQLite on Render | Architecture decision | Data lost on Render redeploy; acceptable for competition |
| No authentication | Architecture decision | UUID in localStorage; no multi-device sync |

### 6.2 Assumptions

- Users have a modern browser (ES2020+ support)
- Users are willing to provide lifestyle data during onboarding
- Google Gemini 1.5 Flash free tier has sufficient quota for demo usage
- India CEA grid emission factor (0.708 kg CO₂/kWh) is representative for target users
- Single-user per browser session is sufficient for competition scope
- IPCC/EPA emission factors are authoritative and accepted by evaluators

---

## 7. Success Metrics

### 7.1 Product Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Baseline accuracy | ≥ 90% of agent analyses correctly identify top emission category | Analyst Agent output vs Carbon Engine data |
| Coaching groundedness | 100% of agent outputs reference user-specific activity data | Agent system prompts enforce grounded responses |
| Mission completion rate | ≥ 50% on accepted missions | `missions` table: completed / (active + completed) |
| Visible progress trend | Downward trend after 7 days of logging | `carbon/trends` endpoint data |
| Calculation trust | 100% of calculations use cited emission factors | Code review: all factors have inline source citations |

### 7.2 Competition Criteria Metrics

| Criterion | Implementation Evidence |
|-----------|----------------------|
| **Code Quality** | TypeScript strict mode, Pydantic v2, layered architecture, single-responsibility modules, consistent naming |
| **Security** | Secrets in `.env`, CORS allowlist, rate limiting middleware, Pydantic input validation, no PII exposure |
| **Efficiency** | Gemini 1.5 Flash, SQLite, async FastAPI, 24hr insight cache, React Query `staleTime=5min` |
| **Testing** | pytest + httpx backend, Vitest + RTL frontend, ≥ 80% coverage on core modules |
| **Accessibility** | shadcn/ui components, ARIA labels, keyboard navigation, WCAG 2.1 AA contrast, focus management |

---

*Document ends.*
