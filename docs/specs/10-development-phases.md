# CarbonSense AI — Development Phases

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. Timeline Overview

**Total duration:** 12 days (June 9 → June 21, 2026)  
**Deadline:** Sunday, June 21, 2026, 11:59 PM IST  
**Maximum submissions:** 3 (each overwrites previous score)

```
 Day 1–2          Day 3–5          Day 6–8         Day 9–11         Day 12
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│  Phase 0   │  │  Phase 1   │  │  Phase 2   │  │  Phase 3   │  │  Phase 4   │
│            │  │            │  │            │  │            │  │            │
│ Foundation │  │ Backend    │  │ Frontend   │  │ Agent      │  │ Polish &   │
│ & Scaffold │  │ Core APIs  │  │ Core UI    │  │ Pipeline   │  │ Submit     │
│            │  │ + Carbon   │  │ + Dashboard│  │ + Chat     │  │            │
│            │  │ Engine     │  │ + Logging  │  │ + Missions │  │            │
└────────────┘  └────────────┘  └────────────┘  └────────────┘  └────────────┘
  Submission 1 →                    ↑ Day 6         ↑ Day 9         ↑ Day 12
                                  (core done)    (agents done)   (final)
```

---

## 2. Phase 0 — Foundation & Scaffold (Days 1–2)

### Objective

Set up the monorepo, tooling, database, and boilerplate so that both backend and frontend can be developed in parallel from Day 3.

### Deliverables

| # | Deliverable | Done When |
|---|---|---|
| 0.1 | Repository created with full directory structure | `git log` shows initial commit with all folders |
| 0.2 | Backend: FastAPI app runs with health endpoint | `GET /api/v1/health` → `{"status":"ok"}` |
| 0.3 | Backend: `config.py` loads all env vars via `pydantic-settings` | `settings.gemini_api_key` is populated |
| 0.4 | Backend: SQLite migration runs on startup | All 5 tables + 4 indexes created |
| 0.5 | Backend: Pydantic schemas defined for all models | `schemas.py` compiles with no errors |
| 0.6 | Frontend: Vite + React + TS project initialized | `npm run dev` shows welcome page |
| 0.7 | Frontend: Tailwind CSS + shadcn/ui configured | Button component renders with correct styles |
| 0.8 | Frontend: React Router with all 6 routes | Navigation between pages works |
| 0.9 | Frontend: Layout with persistent nav header | Nav links visible on all protected pages |
| 0.10 | `.gitignore`, `.env.example`, `README.md` created | Repo clean, no secrets committed |
| 0.11 | GitHub Actions CI workflow (`ci.yml`) | Push triggers lint/test job (may be empty tests initially) |
| 0.12 | Docs: All 12 spec files committed | `docs/specs/` contains all specs |

### Key Files Created

```
backend/app/main.py
backend/app/config.py
backend/app/db/database.py
backend/app/db/migrations/001_initial.sql
backend/app/models/schemas.py
backend/app/api/v1/health.py
frontend/src/App.tsx
frontend/src/components/Layout.tsx
frontend/src/lib/user-session.ts
.github/workflows/ci.yml
.gitignore
README.md
```

### Exit Criteria

- `cd backend && uvicorn app.main:app` starts without errors
- `cd frontend && npm run dev` renders a page with navigation
- `GET http://localhost:8000/api/v1/health` returns 200
- All spec docs are committed

---

## 3. Phase 1 — Backend Core APIs + Carbon Engine (Days 3–5)

### Objective

Build the foundational backend: user CRUD, Carbon Engine, activity logging (form + NL), carbon aggregation endpoints, and core middleware (CORS, rate limiting, error handling).

### Deliverables

| # | Deliverable | Done When |
|---|---|---|
| 1.1 | Carbon Engine with all emission factors | `test_carbon_engine.py` passes with ≥ 90% coverage |
| 1.2 | `POST /api/v1/users` — create user | Integration test passes |
| 1.3 | `GET /api/v1/users/{id}` — get user | Returns full profile |
| 1.4 | `PUT /api/v1/users/{id}` — update user | Updates and returns new profile |
| 1.5 | `POST /api/v1/activities` — log form activity | CO₂ calculated correctly via Carbon Engine |
| 1.6 | `GET /api/v1/activities/{user_id}` — activity history | Paginated, filterable by category |
| 1.7 | `DELETE /api/v1/activities/{id}` — delete activity | Entry removed from database |
| 1.8 | `GET /api/v1/carbon/summary/{user_id}` — monthly summary | Category breakdown with percentages |
| 1.9 | `GET /api/v1/carbon/trends/{user_id}` — daily trend | Array of date/kg pairs for N days |
| 1.10 | `GET /api/v1/carbon/progress/{user_id}` — vs baseline | reduction_pct, vs_india_average_pct |
| 1.11 | CORS middleware configured | Only `ALLOWED_ORIGINS` accepted |
| 1.12 | Rate limiter middleware | 429 response on limit exceeded |
| 1.13 | Global exception handler | `{"detail": "safe message"}` on all errors |
| 1.14 | GeminiService created (function_call + stream) | Module importable, testable with mocks |
| 1.15 | Unit + integration tests | ≥ 25 tests passing |

### Key Files Created

```
backend/app/services/carbon_engine.py
backend/app/services/gemini_service.py
backend/app/api/v1/users.py
backend/app/api/v1/activities.py
backend/app/api/v1/carbon.py
backend/app/middleware/rate_limiter.py
backend/tests/unit/test_carbon_engine.py
backend/tests/unit/test_schemas.py
backend/tests/integration/test_activities_api.py
backend/tests/integration/test_carbon_api.py
backend/tests/integration/test_onboarding_api.py
```

### Exit Criteria

- All carbon engine tests pass: `pytest tests/unit/test_carbon_engine.py -v`
- Activity logging works end-to-end: POST → calculate CO₂ → store → retrieve
- Carbon summary returns correct aggregations
- CORS blocks requests from unlisted origins
- Rate limiter returns 429 after exceeding threshold

---

## 4. Phase 2 — Frontend Core UI + Dashboard (Days 6–8)

### Objective

Build the user-facing experience: onboarding wizard, activity logger (form tab), insights dashboard with all 6 widgets, and the keepalive mechanism.

### Deliverables

| # | Deliverable | Done When |
|---|---|---|
| 2.1 | OnboardingFlow: 4-step wizard | Submits profile → creates user → stores UUID → redirects |
| 2.2 | ProtectedRoute guard | Unauthenticated users redirected to /onboarding |
| 2.3 | Landing page with hero + CTA | "Get Started" button navigates to /onboarding |
| 2.4 | Activity form (structured input) | Selects category/type/amount → submits → shows CO₂ |
| 2.5 | Activity history table | Lists activities with date, category, CO₂, delete button |
| 2.6 | Dashboard: Monthly Footprint Card | Shows total_kg and reduction_pct |
| 2.7 | Dashboard: Category Pie Chart | Recharts PieChart with hover tooltips |
| 2.8 | Dashboard: Trend Line Chart | Recharts LineChart with 7/30/90 day selector |
| 2.9 | Dashboard: Goal Progress Bar | Shows reduction % vs target % |
| 2.10 | Dashboard: Eco Points Card | Shows points + tier label |
| 2.11 | React Query configured | `staleTime=5min`, mutation invalidation |
| 2.12 | Keepalive hook | 14-min ping to /health |
| 2.13 | `api.ts` typed API client | All fetch calls centralized |
| 2.14 | `useCarbon`, `useActivities`, `useUser` hooks | Working with React Query |
| 2.15 | Frontend component tests | ≥ 3 component tests |

### Key Files Created

```
frontend/src/pages/Landing.tsx
frontend/src/pages/Onboarding.tsx
frontend/src/pages/DashboardPage.tsx
frontend/src/pages/LogPage.tsx
frontend/src/components/OnboardingFlow.tsx
frontend/src/components/ActivityForm.tsx
frontend/src/components/ActivityLogger.tsx
frontend/src/components/Dashboard.tsx
frontend/src/components/FootprintPieChart.tsx
frontend/src/components/TrendLineChart.tsx
frontend/src/components/GoalProgressBar.tsx
frontend/src/components/EcoPointsBadge.tsx
frontend/src/hooks/useCarbon.ts
frontend/src/hooks/useActivities.ts
frontend/src/hooks/useUser.ts
frontend/src/hooks/useKeepalive.ts
frontend/src/lib/api.ts
frontend/src/lib/keepalive.ts
frontend/src/types/api.ts
```

### Exit Criteria

- Onboarding flow: fill 4 steps → click submit → user created → redirected to dashboard
- Dashboard renders all 6 widgets with real data from backend
- Activity form: submit → CO₂ calculated → appears in history
- Time range selector on trend chart works (7/30/90 days)
- Keepalive ping visible in browser DevTools network tab
- ≥ 3 frontend component tests pass: `npm run test:run`

---

## 5. Phase 3 — Agent Pipeline + Chat + Missions (Days 9–11)

### Objective

Build the AI intelligence layer: all 4 agents, the orchestrator, SSE streaming, natural language activity parsing, chat interface, and mission center.

### Deliverables

| # | Deliverable | Done When |
|---|---|---|
| 3.1 | BaselineAgent: profile → BaselineResult | Onboarding calculates baseline via Gemini |
| 3.2 | `POST /api/v1/onboarding/baseline` endpoint | Returns baseline with category breakdown |
| 3.3 | AnalystAgent: activities → AnalysisResult | Identifies hotspots and patterns |
| 3.4 | PlannerAgent: analysis → PlanResult | Generates strategies and missions |
| 3.5 | CoachAgent: streaming coaching response | SSE stream to frontend |
| 3.6 | AgentOrchestrator: Analyst → Planner → Coach | Sequential pipeline with cache check |
| 3.7 | `POST /api/v1/agents/analyze` (SSE endpoint) | Returns streaming response |
| 3.8 | Insight cache read/write/invalidation | 24hr TTL, invalidated on new activity |
| 3.9 | `POST /api/v1/activities/parse-nl` | NL description → structured activity via Gemini |
| 3.10 | NL input tab on Activity Logger | Frontend tab for natural language logging |
| 3.11 | Chat page with SSE streaming display | Messages stream token-by-token |
| 3.12 | `POST /api/v1/chat/stream` (SSE endpoint) | Coach Agent with conversation history |
| 3.13 | `useStream` hook | Manages SSE lifecycle, abort, error handling |
| 3.14 | Mission Center page | 3 panels: Available, Active, Completed |
| 3.15 | `POST /api/v1/missions/generate` | Create missions from Planner output |
| 3.16 | `PUT /api/v1/missions/{id}/accept` | Accept mission, set deadline |
| 3.17 | `POST /api/v1/missions/{id}/complete` | Complete mission, award Eco Points |
| 3.18 | Eco Points tier update | Points + tier reflected in nav badge |
| 3.19 | Agent orchestrator tests (mocked Gemini) | ≥ 5 orchestrator tests |

### Key Files Created

```
backend/app/agents/baseline_agent.py
backend/app/agents/analyst_agent.py
backend/app/agents/planner_agent.py
backend/app/agents/coach_agent.py
backend/app/services/agent_orchestrator.py
backend/app/services/insights_cache.py
backend/app/api/v1/onboarding.py
backend/app/api/v1/agents.py
backend/app/api/v1/chat.py
backend/app/api/v1/missions.py
frontend/src/pages/ChatPage.tsx
frontend/src/pages/MissionsPage.tsx
frontend/src/components/ChatInterface.tsx
frontend/src/components/NLActivityInput.tsx
frontend/src/components/MissionCenter.tsx
frontend/src/components/MissionCard.tsx
frontend/src/hooks/useStream.ts
frontend/src/hooks/useMissions.ts
```

### Exit Criteria

- Full agent pipeline: click "Analyze" → Analyst → Planner → Coach streams response
- Chat: type message → Coach responds with streaming tokens
- NL logging: type "drove 25km in diesel car" → parsed → logged → CO₂ shown
- Missions: generate → accept → complete → Eco Points updated
- Insight cache: second analysis within 24hr hits cache (faster response)
- ≥ 5 orchestrator tests pass (Gemini mocked)

---

## 6. Phase 4 — Polish, Testing & Submit (Day 12)

### Objective

Final pass: accessibility, full test coverage, performance optimization, documentation, and competition submission.

### Deliverables

| # | Deliverable | Done When |
|---|---|---|
| 4.1 | ARIA labels on all charts | Every Recharts component has aria-label |
| 4.2 | Keyboard navigation verified | Tab through all pages works correctly |
| 4.3 | Focus management on route change | Focus moves to `<h1>` on navigation |
| 4.4 | Color contrast check | All text passes 4.5:1 ratio |
| 4.5 | Semantic HTML audit | `<main>`, `<nav>`, `<section>`, single `<h1>` per page |
| 4.6 | Full backend test suite | ≥ 40 tests, coverage report clean |
| 4.7 | Full frontend test suite | ≥ 8 component tests |
| 4.8 | GitHub Actions CI green | All tests pass on push to main |
| 4.9 | Lighthouse audit | Performance > 90, Accessibility > 90 |
| 4.10 | README.md finalized | Documents: vertical, approach, how it works, assumptions |
| 4.11 | Deploy frontend to Vercel | Production URL working |
| 4.12 | Deploy backend to Render | Production URL working + health check passing |
| 4.13 | End-to-end smoke test on production | Full flow: onboard → log → analyze → chat → mission |
| 4.14 | Repo size check | `< 10 MB` confirmed |
| 4.15 | Submit to PromptWars | Final submission (attempt 3) |

### Exit Criteria

- All tests pass: `pytest` and `npm run test:run`
- Deployed URLs are live and functional
- Lighthouse: Performance > 90, Accessibility > 90
- README.md is complete and professional
- Repo size < 10 MB
- Competition submission confirmed

---

## 7. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Gemini API rate limit hit during development | Medium | Medium | Use mocks in tests; real API only for manual testing |
| Render free tier cold start delays demo | High | Medium | Keepalive ping every 14 min |
| SQLite data loss on Render redeploy | High | Low | Acceptable for competition; seed script for demo data |
| Tailwind + shadcn/ui setup issues | Low | Low | Use well-documented setup guides |
| Frontend bundle > 500 KB | Low | Low | Lazy load routes; tree-shake unused components |
| CI pipeline flaky due to Gemini | Medium | Medium | Mock all Gemini calls in CI; use `GEMINI_API_KEY` secret |
| Running out of time on Phase 3 | Medium | High | Prioritize core pipeline (Analyst + Coach); defer missions to P1 |

---

## 8. Dependencies Between Phases

```
Phase 0 ──────────────→ Phase 1 ──────────────→ Phase 2
(scaffold)               (backend APIs)           (frontend UI)
                              │                        │
                              └──────────┬─────────────┘
                                         │
                                         ▼
                                      Phase 3
                                   (agents + AI)
                                         │
                                         ▼
                                      Phase 4
                                   (polish + submit)
```

**Critical path:** Phase 1 (backend APIs) must be complete before Phase 2 can start API integration. Phase 3 depends on both backend APIs and frontend UI being functional. Phase 4 is pure polish — all features must be done by end of Phase 3.

---

*Document ends.*
