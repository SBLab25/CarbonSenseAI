# CarbonSense AI — Product Requirements Document

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Problem Statement:** Carbon Footprint Awareness Platform  
**Deadline:** Sun, Jun 21, 2026 11:59 PM IST  
**Author:** Sovan Bhakta

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Vision](#3-product-vision)
4. [Target Users](#4-target-users)
5. [Goals & Success Metrics](#5-goals--success-metrics)
6. [Feature Requirements](#6-feature-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [User Stories](#8-user-stories)
9. [Out of Scope (MVP)](#9-out-of-scope-mvp)
10. [Timeline & Milestones](#10-timeline--milestones)

---

## 1. Executive Summary

CarbonSense AI is a multi-agent sustainability coaching platform that transforms passive carbon tracking into an active, AI-driven behavior change experience. Rather than presenting users with static emission reports, the platform acts as a personalized team of AI sustainability experts that continuously analyzes lifestyle patterns, generates adaptive reduction plans, and coaches users toward measurable environmental goals.

The core differentiator: where every other tool stops at calculation, CarbonSense AI begins coaching.

---

## 2. Problem Statement

### 2.1 Current State of Carbon Tracking

Most existing carbon footprint tools follow a linear, passive pattern:

```
User enters data  →  Carbon calculated  →  Generic report shown  →  User leaves
```

This creates three fundamental failures:

| Problem | User Impact |
|---------|-------------|
| No contextual intelligence | Every user receives the same generic advice regardless of their specific lifestyle |
| No continuity | Each session starts from scratch; the tool has no memory of prior behavior |
| No behavioral engagement | Static numbers do not motivate action or drive sustainable change |

### 2.2 The Opportunity

A substantial segment of climate-conscious individuals want to act sustainably but lack personalized, actionable guidance. Existing tools optimize for data collection, not behavior change. There is a clear gap for an AI-first platform that acts as a continuous sustainability advisor — one that knows the user, tracks their progress, and coaches them forward.

### 2.3 The CarbonSense Difference

Consider a user named Alex.

A standard tool would say:

> *"Your monthly footprint is 215 kg CO₂."*

CarbonSense AI says:

> *"Transportation contributes 52% of your footprint. By replacing 2 weekly car trips with public transport, you could reduce emissions by 18 kg/month. Want me to create a 30-day reduction plan?"*

Then two weeks later:

> *"You've successfully reduced transport emissions by 8%. Let's increase your goal from 10% to 15%."*

This is the difference between a calculator and a coach.

---

## 3. Product Vision

**Vision Statement:**  
CarbonSense AI turns carbon awareness into a continuous coaching journey — making sustainable living achievable through personalized AI intelligence, not generic advice.

**Mission:**  
Empower individuals to understand and reduce their environmental impact through adaptive AI coaching that meets them where they are and guides them toward where they want to be.

---

## 4. Target Users

### 4.1 Primary: Climate-Conscious Individual

- Age 20–40, urban or suburban
- Aware of climate change and personally motivated to reduce their impact
- Frustrated by the complexity and genericness of existing carbon tools
- Willing to log activities consistently if the feedback is meaningful and personalized
- **Goal:** Reduce personal carbon footprint by a specific, measurable amount

### 4.2 Secondary: Sustainability-Curious Learner

- New to carbon tracking, exploring sustainable living
- Needs education alongside action
- Responds well to gamification, milestones, and visible progress
- **Goal:** Understand their environmental impact and take first steps toward change

---

## 5. Goals & Success Metrics

### 5.1 Product Goals

| Goal | Metric | Target |
|------|--------|--------|
| Users understand their footprint | Correctly identifies their top emission category | ≥ 90% accuracy in agent analysis |
| AI coaching is contextual | Every recommendation references user's specific activity data | 100% of agent outputs grounded in user data |
| Users take action | Mission acceptance and completion rate | ≥ 50% completion on accepted missions |
| Progress is visible | Dashboard shows measurable reduction trend | Visible downward trend after 7 days of logging |
| Platform is trusted | Carbon calculations use cited emission factors | 100% of calculations reference IPCC/EPA data |

### 5.2 Competition Evaluation Goals

| Criterion | Our Approach |
|-----------|--------------|
| **Code Quality** | TypeScript strict mode frontend, Pydantic-validated backend, clean module separation with single responsibility |
| **Security** | All secrets in `.env`, CORS allowlist configured, AI endpoint rate limiting (10 req/min/user), full input validation |
| **Efficiency** | Gemini 1.5 Flash (fastest/cheapest Gemini tier), SQLite (zero-dependency persistence), async throughout, 24hr insight caching |
| **Testing** | pytest for backend (carbon engine + API routes), Vitest for frontend, ≥ 80% coverage on core modules |
| **Accessibility** | shadcn/ui components, ARIA labels on all interactive elements, keyboard navigation, WCAG 2.1 AA color contrast |

---

## 6. Feature Requirements

### F1 — AI Sustainability Coach (Conversational Interface)

**Priority:** P0 — Must Have

The primary user-facing interface. A streaming chat assistant powered by Google Gemini 1.5 Flash that serves as the orchestrator between the user and the specialized agent pipeline. All natural language interaction flows through this module.

**Functional Requirements:**

| ID | Requirement |
|----|-------------|
| FR-1.1 | Accept free-form natural language input from the user |
| FR-1.2 | Stream responses token-by-token via Server-Sent Events (SSE) for real-time feedback |
| FR-1.3 | Maintain conversation history within a session (last 10 turns retained in context) |
| FR-1.4 | Trigger the full agent pipeline (Analyst → Planner → Coach) on explicit analysis requests |
| FR-1.5 | Parse natural language activity descriptions into structured entries via Gemini function calling |
| FR-1.6 | Surface agent pipeline results through the Coach Agent's conversational output |

**Acceptance Criteria:**
- First response token streamed within 2 seconds of user submission
- Full agent pipeline completes and Coach response begins streaming within 10 seconds
- Conversation context is coherently maintained across all turns in a session

---

### F2 — User Onboarding & Baseline Agent

**Priority:** P0 — Must Have

A 4-step guided onboarding flow that collects the user's profile data and runs the Baseline Agent to establish their starting carbon footprint before any activity logging begins. This ensures all subsequent coaching is personalized from the very first interaction.

**Functional Requirements:**

| ID | Requirement |
|----|-------------|
| FR-2.1 | Collect user profile: name, country, city, lifestyle type (urban / suburban / rural) |
| FR-2.2 | Collect transport habits: primary mode, estimated weekly distance |
| FR-2.3 | Collect food habits: diet type (vegan / vegetarian / mixed / high meat) |
| FR-2.4 | Collect energy usage: monthly electricity kWh estimate, heating type (LPG / electric / none) |
| FR-2.5 | Generate a session-based user UUID (stored in localStorage — no authentication required for MVP) |
| FR-2.6 | Baseline Agent analyzes profile data and calculates initial estimated footprint per category |
| FR-2.7 | Store baseline as the permanent reference point for all future progress calculations |
| FR-2.8 | Skip onboarding if a valid user UUID already exists in localStorage |

**Acceptance Criteria:**
- Full onboarding flow completable in under 2 minutes
- Baseline footprint is calculated, stored, and visible before the dashboard loads for the first time
- All subsequent agent outputs reference the baseline as the starting point

---

### F3 — Activity Logger

**Priority:** P0 — Must Have

A dual-input system for logging sustainability-related activities. Supports both structured form input and natural language input. Natural language entries are automatically parsed by Gemini function calling into structured JSON before storage.

**Activity Categories:**

| Category | Types |
|----------|-------|
| Transport | Car (petrol/diesel/electric), bus, train, domestic flight, international flight, motorcycle, bicycle, walking |
| Energy | Electricity (kWh), natural gas, LPG |
| Food | Beef, lamb, pork, chicken, fish, dairy, eggs, vegetables, fruits, grains, legumes |
| Shopping | Electronics, clothing, household items |

**Functional Requirements:**

| ID | Requirement |
|----|-------------|
| FR-3.1 | Structured form input for all four categories with appropriate unit selection |
| FR-3.2 | Natural language input ("I drove 20 km to work today") auto-parsed to structured JSON via Gemini function calling |
| FR-3.3 | Carbon kg CO₂ calculated by Carbon Engine immediately on save |
| FR-3.4 | Activity history view: paginated list, filterable by category and date range |
| FR-3.5 | Delete activity entries (with carbon total recalculation) |
| FR-3.6 | Activity log invalidates the 24-hour insight cache on save |

**Acceptance Criteria:**
- Natural language parsing accuracy ≥ 85% on common activity descriptions
- Carbon value calculated and displayed within 500ms of saving
- Activity history loads within 500ms for up to 100 entries

---

### F4 — Carbon Engine

**Priority:** P0 — Must Have

The deterministic analytical core. Uses IPCC/EPA/peer-reviewed emission factors to produce accurate, citeable carbon values for every activity type. This module has no AI dependency — it is pure calculation logic, making it independently testable and auditable.

**Emission Factor Sources:**

| Category | Source |
|----------|--------|
| Transport | IPCC AR6 (2022), UK DEFRA Conversion Factors 2023 |
| Energy | IEA (2023), India CEA grid emission factor (0.708 kg CO₂/kWh) |
| Food | Poore & Nemecek, *Science* (2018); Our World in Data |
| Shopping | Berners-Lee, *How Bad Are Bananas?* (2020) |

**Key Emission Factors:**

| Type | Factor | Unit |
|------|--------|------|
| Car (petrol) | 0.21 kg CO₂ | per km |
| Car (electric) | 0.05 kg CO₂ | per km |
| Bus | 0.089 kg CO₂ | per km |
| Train | 0.041 kg CO₂ | per km |
| Domestic flight | 0.255 kg CO₂ | per km |
| Electricity (India) | 0.708 kg CO₂ | per kWh |
| Beef | 27.0 kg CO₂ | per kg food |
| Chicken | 6.9 kg CO₂ | per kg food |
| Vegetables | 2.0 kg CO₂ | per kg food |

**Functional Requirements:**

| ID | Requirement |
|----|-------------|
| FR-4.1 | Calculate kg CO₂ for any activity given: category, type, amount, and unit |
| FR-4.2 | Aggregate monthly footprint totals broken down by category |
| FR-4.3 | Calculate percentage share of each category in total footprint |
| FR-4.4 | Generate historical trend data for 7-day, 30-day, and 90-day windows |
| FR-4.5 | Track progress as percentage reduction from baseline footprint |
| FR-4.6 | Compare user's footprint against India national average (1.9 tonnes CO₂/year) |
| FR-4.7 | All emission factors documented with source citations in code comments |

**Acceptance Criteria:**
- Calculation is fully deterministic (identical inputs always produce identical outputs)
- Monthly aggregation handles sparse data (days with no logged activities) gracefully with zero fill
- All emission factors in code match published source values within 5% tolerance

---

### F5 — Multi-Agent Intelligence Layer

**Priority:** P0 — Must Have

A custom-built sequential agent pipeline orchestrated without external framework dependencies. Four specialized agents collaborate, each receiving only the typed, validated output of the previous stage. This architecture demonstrates genuine agentic AI reasoning rather than a single-prompt chatbot.

**Agent Pipeline:**

```
[Onboarding]
Baseline Agent  ──────────────────────────→  Initial footprint estimate
                                                       ↓
[On Analysis Request]
Carbon Analyst Agent  ────────────────────→  Hotspot analysis + behavioral patterns
                                                       ↓
Planner Agent  ───────────────────────────→  3–5 specific reduction strategies + impact estimates
                                                       ↓
Coach Agent  ─────────────────────────────→  Personalized message + goal + motivation (streamed)
```

**Agent Definitions:**

| Agent | Input | Output Schema | Gemini Mode |
|-------|-------|---------------|-------------|
| Baseline Agent | User profile (lifestyle, transport, food, energy) | `BaselineResult`: estimated monthly footprint per category | Function calling → structured JSON |
| Carbon Analyst Agent | Activity history + footprint summary + baseline | `AnalysisResult`: top emission categories, behavioral patterns, hotspot flags | Function calling → structured JSON |
| Planner Agent | `AnalysisResult` + user profile | `PlanResult`: list of `ReductionStrategy` objects with type, action, estimated_monthly_saving_kg, difficulty | Function calling → structured JSON |
| Coach Agent | `AnalysisResult` + `PlanResult` + progress vs baseline | Natural language message: greeting, key insight, primary recommendation, motivational close | Standard generation (streamed via SSE) |

**Functional Requirements:**

| ID | Requirement |
|----|-------------|
| FR-5.1 | Agents communicate exclusively via validated Pydantic models — no free-text agent-to-agent communication |
| FR-5.2 | Each agent receives only the context it requires (principle of minimal context) |
| FR-5.3 | Full pipeline triggered and completed within a single `POST /api/v1/agents/analyze` call |
| FR-5.4 | Agent outputs cached for 24 hours per user; cache invalidated on any new activity log |
| FR-5.5 | Coach Agent response streamed to frontend via SSE as it generates |
| FR-5.6 | Pipeline validates each stage output against its Pydantic schema before passing to next agent |
| FR-5.7 | Rate limit: maximum 3 full pipeline runs per user per hour |

**Acceptance Criteria:**
- Full pipeline (Analyst + Planner + Coach first token) completes within 10 seconds
- Each agent output validates against its Pydantic schema 100% of the time
- Pipeline gracefully handles Gemini API errors with structured error responses (never returns raw exception text to frontend)

---

### F6 — Insights Dashboard

**Priority:** P0 — Must Have

A visual analytics panel that presents the user's carbon footprint data, trends, and progress against goals. Built with Recharts for interactive, accessible data visualization.

**Dashboard Widgets:**

| Widget | Type | Description |
|--------|------|-------------|
| Current Monthly Footprint | Metric card | kg CO₂ this month vs last month vs baseline |
| Category Breakdown | Pie chart (Recharts) | Percentage share of Transport, Energy, Food, Shopping |
| Historical Trend | Line chart (Recharts) | Daily totals over 7 / 30 / 90 days |
| Goal Progress | Progress bar | % reduction achieved toward user's target |
| Top Emission Source | Highlight card | Highest-impact category with AI-generated micro-tip |
| Eco Points Balance | Metric card | Total accumulated points with tier label |

**Functional Requirements:**

| ID | Requirement |
|----|-------------|
| FR-6.1 | Dashboard loads with latest aggregated data on every visit (client-side fetch on mount) |
| FR-6.2 | Time range selector controls Historical Trend chart (7 / 30 / 90 days) |
| FR-6.3 | All charts include hover tooltips with exact values |
| FR-6.4 | Empty state shown for new users who have not yet logged activities, with prompt to log first activity |
| FR-6.5 | All charts have ARIA labels and are keyboard-navigable |

**Acceptance Criteria:**
- Dashboard renders within 1 second when data is available
- Charts degrade gracefully with sparse data (1–3 data points)
- All chart colors pass WCAG 2.1 AA contrast ratio (≥ 4.5:1)

---

### F7 — Mission Center

**Priority:** P1 — Should Have for MVP

A gamified action system that converts Planner Agent recommendations into specific, time-bound sustainability challenges. Completing missions earns Eco Points, reinforces behavior change, and provides a feedback loop between AI recommendations and user action.

**Example Missions:**

| Mission | Category | Duration | Eco Points | Est. CO₂ Impact |
|---------|----------|----------|------------|-----------------|
| Green Commute Challenge | Transport | 7 days | 150 pts | −8 kg CO₂ |
| Meat-Free Week | Food | 7 days | 200 pts | −5 kg CO₂ |
| Energy Audit Week | Energy | 7 days | 100 pts | −3 kg CO₂ |
| No Fast Fashion Month | Shopping | 14 days | 250 pts | −10 kg CO₂ |

**Functional Requirements:**

| ID | Requirement |
|----|-------------|
| FR-7.1 | Planner Agent generates 2–3 mission suggestions based on user's top emission categories |
| FR-7.2 | User can accept or dismiss each mission suggestion |
| FR-7.3 | Accepted missions have a deadline; they expire automatically if not completed |
| FR-7.4 | Mission completion is user-confirmed and records an activity entry that reduces measured footprint |
| FR-7.5 | Eco Points are awarded and balance updated immediately on completion |
| FR-7.6 | Eco Points balance and tier (Seedling / Sapling / Tree / Forest) visible in navigation header |
| FR-7.7 | Active missions displayed in a dedicated panel with progress indicators and days remaining |

**Acceptance Criteria:**
- Missions are generated using actual user activity data — no generic defaults
- Points balance updates without a full page reload
- Expired missions move to a "Past Missions" section, not deleted

---

## 7. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | First Contentful Paint ≤ 2s (Vercel CDN). API P95 latency ≤ 500ms (non-AI endpoints). AI first token streamed ≤ 2s. |
| **Security** | API keys in `.env` only, never committed. CORS configured to allowed origins only. AI endpoints rate-limited to 10 requests/min/user. All request bodies validated with Pydantic. No sensitive data in frontend localStorage beyond user UUID. |
| **Reliability** | Backend on Render with frontend-driven 14-minute keepalive ping to `/api/v1/health`. Frontend on Vercel (99.9% SLA). |
| **Accessibility** | WCAG 2.1 AA compliance. Full keyboard navigation. ARIA labels on all interactive elements and data visualizations. Minimum color contrast ratio 4.5:1. |
| **Browser Support** | Chrome 120+, Firefox 120+, Safari 17+, Edge 120+. |
| **Repository** | Single branch (`main`). Total size ≤ 10 MB. Public GitHub repository. README documents vertical chosen, approach, how the solution works, and assumptions made. |
| **Testability** | ≥ 80% test coverage on Carbon Engine and agent orchestrator. All API routes have at least one integration test. |

---

## 8. User Stories

**US-01 (Onboarding):**  
As a new user, I want to complete onboarding in under 2 minutes so I can immediately see my estimated carbon footprint before I log any activities.

**US-02 (Natural Language Logging):**  
As a user, I want to describe my activities naturally ("I flew to Delhi this morning") without filling out complex forms, so that logging feels effortless.

**US-03 (Hotspot Analysis):**  
As a user, I want the AI to identify which specific part of my lifestyle creates the most emissions so I know exactly where to focus my efforts.

**US-04 (Personalized Planning):**  
As a user, I want a concrete, achievable plan to reduce my footprint by a meaningful percentage this month — not generic tips I could read anywhere.

**US-05 (Gamification):**  
As a user, I want to earn Eco Points for completing sustainability challenges so I stay motivated beyond the initial novelty.

**US-06 (Progress Tracking):**  
As a user, I want to see my emissions trend on a chart so I can confirm whether my actions are making a real, measurable difference.

**US-07 (Continuous Coaching):**  
As a user, I want to ask the AI coach follow-up questions at any time so I can deepen my understanding of sustainable living as I go.

**US-08 (Goal Setting):**  
As a user, I want to set a specific emissions reduction goal for the month so the AI can calibrate its recommendations to that target.

---

## 9. Out of Scope (MVP)

The following features are explicitly deferred to Version 2:

- Multi-user authentication (JWT, OAuth2, magic links)
- Social features: community leaderboards, friend challenges, sharing
- Carbon offset purchasing and third-party verification
- External API integrations (Google Maps commute tracking, utility bill import, receipt scanning)
- Native mobile application (iOS/Android)
- Long-term predictive modeling (6-month, 1-year projections using ML)
- Organizational/team carbon tracking
- Real-time emissions data (connected IoT devices, smart meters)
- Carbon credit marketplace

---

## 10. Timeline & Milestones

| Day | Date | Milestone | Deliverable |
|-----|------|-----------|-------------|
| 1 | Jun 09 | Foundation | Project scaffold, DB schema, Carbon Engine implementation + tests |
| 2 | Jun 10 | Core Backend | All API routes, Pydantic schemas, SQLite setup, Agent orchestrator |
| 3 | Jun 11 | Gemini Integration | Baseline Agent, Analyst Agent, Planner Agent working with function calling |
| 4 | Jun 12 | Frontend Shell | React app, Onboarding flow, Activity Logger, routing |
| 5 | Jun 13 | AI Frontend Integration | Coach Agent streaming SSE, Dashboard with Recharts |
| 6 | Jun 14 | Missions + Polish | Mission Center, Eco Points, accessibility audit |
| 7 | Jun 14–15 | **First Submission** | **Deployed to Vercel + Render, GitHub repo submitted** |
| 8–12 | Jun 16–20 | Iteration | Bug fixes, test coverage increase, attempt 2 or 3 if score improves |

> **Strategy Note:** The score multiplier decays over time from the submission opening date (Jun 08, 5PM IST). Submitting by Day 7 (Jun 14–15) captures a meaningful multiplier advantage over the deadline. The first submission does not have to be perfect — it locks in the multiplier, and subsequent attempts (up to 3 total) overwrite the score.

---

*Document ends.*
