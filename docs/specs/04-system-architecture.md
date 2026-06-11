# CarbonSense AI — System Architecture

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. Architecture Overview (C4 Context Level)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                           SYSTEM CONTEXT                              ║
╚═══════════════════════════════════════════════════════════════════════╝

  ┌──────────────┐
  │    User       │  Climate-conscious individual
  │  (Browser)    │  Chrome 120+ / Firefox 120+ / Safari 17+ / Edge 120+
  └──────┬───────┘
         │ HTTPS
         │ REST (application/json) + SSE (text/event-stream)
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         CARBONSENSE AI                                  │
│                                                                          │
│  Multi-agent sustainability coaching platform that helps individuals     │
│  track, understand, and reduce their carbon footprint through            │
│  personalized AI coaching — not generic calculators.                     │
└───────────────────────────┬──────────────────┬─────────────────────────┘
                            │                  │
               ┌────────────┘                  └────────────┐
               ▼                                            ▼
    ┌──────────────────────┐                  ┌──────────────────────────┐
    │  Google Gemini 1.5   │                  │  SQLite (Render disk)    │
    │  Flash API           │                  │                          │
    │                      │                  │  Persistent on-disk      │
    │  · Function calling  │                  │  users, activities,      │
    │  · Streaming gen     │                  │  insights_cache,         │
    │  · Standard gen      │                  │  missions, goals         │
    └──────────────────────┘                  └──────────────────────────┘
```

### External Actors and Systems

| Actor/System | Role | Protocol |
|---|---|---|
| User (Browser) | Climate-conscious individual using the platform | HTTPS REST + SSE |
| Google Gemini 1.5 Flash | AI reasoning engine for agents and NL parsing | Server-to-server HTTPS (Gemini SDK) |
| SQLite (Render disk) | Persistent data store (5 tables) | Local file I/O via `aiosqlite` |
| Vercel CDN | Static asset delivery for React SPA | Build-time deploy; zero runtime coupling |
| Render | Hosts FastAPI process and SQLite file | Platform deployment |

---

## 2. Container Architecture (C4 Container Level)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                           CONTAINER VIEW                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

  User Browser
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Single-Page Application                              │
  │              React 18 + TypeScript + Vite (on Vercel)                   │
  │                                                                          │
  │  Responsibilities:                                                       │
  │  · Render all UI (Landing, Onboarding, Dashboard, Chat, Log, Missions) │
  │  · Manage session UUID in localStorage                                  │
  │  · Stream SSE responses to chat and agent UI via useStream hook         │
  │  · Keepalive ping every 14 minutes (useKeepalive hook)                  │
  │  · Cache server state with React Query (staleTime=5min)                 │
  └────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTPS REST (JSON)
                                    │ HTTPS SSE (text/event-stream)
                                    ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                      API + Business Layer                               │
  │                FastAPI Python 3.11 (on Render)                          │
  │                                                                          │
  │  Responsibilities:                                                       │
  │  · Serve all REST API endpoints under /api/v1                           │
  │  · Orchestrate multi-agent pipeline (AgentOrchestrator)                 │
  │  · Apply CORS, rate limiting, Pydantic input validation                 │
  │  · Centralize all Gemini API calls via GeminiService                    │
  │  · Calculate carbon via CarbonEngine (deterministic, AI-free)           │
  │  · Read/write data via SQLite (aiosqlite)                               │
  └────────────┬──────────────────────────────────┬──────────────────────┘
               │                                   │
               ▼                                   ▼
    ┌──────────────────────┐          ┌──────────────────────────┐
    │   SQLite DB           │          │  Gemini 1.5 Flash API    │
    │  (Render disk)        │          │  (Google AI Studio)      │
    │                       │          │                          │
    │  Tables:              │          │  · function_call()       │
    │  · users              │          │  · stream_generate()     │
    │  · activities         │          │  · generate_content()    │
    │  · insights_cache     │          └──────────────────────────┘
    │  · missions           │
    │  · goals              │
    └──────────────────────┘
```

### Container Communication Protocols

| From → To | Protocol | Format | Notes |
|---|---|---|---|
| Browser → FastAPI | HTTPS | JSON body / query params | Standard REST |
| Browser → FastAPI (streaming) | HTTPS SSE | `text/event-stream` | Coach Agent + chat |
| Browser → FastAPI (keepalive) | HTTPS GET | No body; expects `{"status":"ok"}` | Every 14 minutes |
| FastAPI → Gemini API | HTTPS | Gemini SDK (JSON/HTTP2) | Server-side only |
| FastAPI → SQLite | File I/O | `aiosqlite` async API | Local disk |

---

## 3. Component Architecture — Backend

### 3.1 Layer Model

```
┌──────────────────────────────────────────────────────┐
│              API Layer (app/api/v1/*.py)               │
│   HTTP concerns: routing, validation, SSE framing,    │
│   rate limiting, error shaping                         │
├──────────────────────────────────────────────────────┤
│           Service Layer (app/services/*.py)            │
│   Business logic: orchestration, caching,              │
│   carbon calculation, Gemini integration               │
├──────────────────────────────────────────────────────┤
│            Agent Layer (app/agents/*.py)               │
│   AI reasoning: each agent is a standalone class       │
│   owning its schema + system prompt                    │
├──────────────────────────────────────────────────────┤
│           Domain Layer (app/models/*.py)               │
│   Pydantic schemas for every contract between layers   │
│   (never raw dicts)                                    │
├──────────────────────────────────────────────────────┤
│       Infrastructure Layer (app/db/*.py)               │
│   Database connection, migration runner,               │
│   raw SQL query helpers                                │
└──────────────────────────────────────────────────────┘
```

### 3.2 Layer Communication Rules

| From Layer | Can Call | Cannot Call |
|---|---|---|
| API Layer | Service Layer, Domain Layer | Agent Layer directly, Infrastructure Layer |
| Service Layer | Agent Layer, Domain Layer, Infrastructure Layer | API Layer |
| Agent Layer | GeminiService (Service), Domain Layer | Database directly, API Layer |
| Domain Layer | Nothing (pure data models) | Any layer |
| Infrastructure Layer | Nothing upward | — |

### 3.3 Backend Module Map

```
backend/app/
├── main.py                    ← FastAPI factory + CORS + router registration + startup init_db
├── config.py                  ← pydantic-settings: all env vars with validation
├── api/v1/
│   ├── __init__.py
│   ├── health.py              ← GET /health (keepalive)
│   ├── users.py               ← POST /users, GET /users/{id}, PUT /users/{id}
│   ├── onboarding.py          ← POST /onboarding/baseline
│   ├── activities.py          ← POST /activities, POST /activities/parse-nl, GET /activities/{id}, DELETE
│   ├── carbon.py              ← GET /carbon/summary/{id}, GET /carbon/trends/{id}, GET /carbon/progress/{id}
│   ├── agents.py              ← POST /agents/analyze (SSE), GET /agents/insights/{id}
│   ├── missions.py            ← GET /missions/{id}, POST /missions/generate, PUT /missions/{id}/accept, POST /missions/{id}/complete
│   └── chat.py                ← POST /chat/stream (SSE)
├── services/
│   ├── gemini_service.py      ← All Gemini API calls: function_call(), stream_generate()
│   ├── carbon_engine.py       ← Deterministic emission calculations (AI-free)
│   ├── agent_orchestrator.py  ← Sequential pipeline: Analyst → Planner → Coach
│   └── insights_cache.py      ← 24-hour cache read/write/invalidation
├── agents/
│   ├── baseline_agent.py      ← estimate(profile) → BaselineResult
│   ├── analyst_agent.py       ← analyze(context) → AnalysisResult
│   ├── planner_agent.py       ← plan(context, analysis) → PlanResult
│   └── coach_agent.py         ← coach_stream(context, analysis, plan) → AsyncGenerator[str]
├── models/
│   ├── schemas.py             ← All Pydantic request/response/inter-agent models
│   └── db_models.py           ← SQLite table definitions
├── db/
│   ├── database.py            ← Async connection (aiosqlite), init_db(), get_db()
│   └── migrations/
│       └── 001_initial.sql    ← Full CREATE TABLE IF NOT EXISTS schema
└── middleware/
    └── rate_limiter.py        ← In-memory sliding window rate limiter
```

### 3.4 Error Handling Architecture

```python
# Domain: safe error types (app/models/schemas.py)
class CarbonSenseError(Exception):
    def __init__(self, user_message: str, log_detail: str):
        self.user_message = user_message
        self.log_detail = log_detail

class GeminiError(CarbonSenseError): pass
class ValidationError(CarbonSenseError): pass
class RateLimitError(CarbonSenseError): pass

# API layer: global exception handler (app/main.py)
@app.exception_handler(CarbonSenseError)
async def carbon_sense_error_handler(request, exc: CarbonSenseError):
    logger.error(f"[{type(exc).__name__}] {exc.log_detail}")
    return JSONResponse(
        status_code=422 if isinstance(exc, ValidationError) else
                     429 if isinstance(exc, RateLimitError) else 500,
        content={"detail": exc.user_message}
    )
```

**Rule:** Raw exception text never reaches the frontend. All errors are shaped into `{"detail": "user-safe message"}`.

---

## 4. Component Architecture — Frontend

### 4.1 Application Shell

```
App.tsx (root)
├── useKeepalive()              ← starts 14-min ping on mount
├── QueryClientProvider          ← React Query context (staleTime=5min)
├── Router (React Router v6)
│   ├── /                      → Landing.tsx
│   ├── /onboarding            → Onboarding.tsx  (redirects to /dashboard if session exists)
│   ├── /dashboard             → DashboardPage.tsx  (protected)
│   ├── /chat                  → ChatPage.tsx       (protected)
│   ├── /log                   → LogPage.tsx        (protected)
│   └── /missions              → MissionsPage.tsx   (protected)
└── Layout.tsx                  ← persistent nav header with EcoPointsBadge
```

### 4.2 Component Hierarchy

```
Layout.tsx
├── NavHeader
│   ├── NavLink → /dashboard
│   ├── NavLink → /chat
│   ├── NavLink → /log
│   ├── NavLink → /missions
│   └── EcoPointsBadge (points + tier)
└── <Outlet />  ← renders current route component
    ├── DashboardPage
    │   ├── MetricCard (monthly footprint)
    │   ├── FootprintPieChart (Recharts PieChart)
    │   ├── TrendLineChart (Recharts LineChart)
    │   ├── GoalProgressBar
    │   ├── TopEmissionCard
    │   └── EcoPointsCard
    ├── ChatPage
    │   └── ChatInterface
    │       ├── MessageList
    │       ├── StreamingDisplay
    │       └── MessageInput
    ├── LogPage
    │   └── ActivityLogger
    │       ├── ActivityForm (structured input)
    │       ├── NLActivityInput (natural language)
    │       └── ActivityHistoryTable
    └── MissionsPage
        └── MissionCenter
            ├── MissionCard (×N)
            └── EcoPointsBalance
```

### 4.3 State Architecture

```
Server State (React Query)              Local State (useState / useReducer)
─────────────────────────────            ──────────────────────────────────────
Carbon summary & trends                 Onboarding current step
Activity history                        Chat message draft
Active missions                         Activity form fields
User profile                            NL input text
Eco points balance                      Dashboard time range selection
                                         Streaming content buffer
```

### 4.4 Custom Hooks

| Hook | Responsibility | Key API Calls |
|------|---------------|---------------|
| `useCarbon()` | Fetch/cache carbon summary + trends | `GET /carbon/summary`, `GET /carbon/trends` |
| `useActivities()` | CRUD operations on activity log | `POST /activities`, `GET /activities/{id}` |
| `useStream()` | Manage SSE connection lifecycle | `POST /chat/stream`, `POST /agents/analyze` |
| `useMissions()` | Fetch, accept, complete missions | `GET /missions/{id}`, `PUT /missions/{id}/accept` |
| `useUser()` | Fetch user profile and session info | `GET /users/{id}` |
| `useKeepalive()` | Initialize 14-min backend ping | `GET /health` |

---

## 5. Multi-Agent Pipeline Architecture

```
User triggers "Analyze My Footprint"
         │
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      AGENT ORCHESTRATOR                                 │
│                  AgentOrchestrator.run_pipeline(user_id)                │
└────┬───────────────────────────────────────────────────────────────┬───┘
     │                                                                │
     │ 1. Check insight cache                                         │
     │    ├── HIT: skip Stage 1+2, go to Stage 3 with cached data   │
     │    └── MISS: run full pipeline                                 │
     │                                                                │
     ▼                                                                │
STAGE 1: ANALYST AGENT                                                │
  Class:   AnalystAgent  (app/agents/analyst_agent.py)                │
  Input:   UserContext                                                │
           ├── profile: UserProfile                                   │
           ├── baseline_footprint: FootprintSummary                   │
           ├── current_footprint: FootprintSummary                    │
           ├── recent_activities: list[ActivityRecord] (30 days)      │
           └── progress_pct: float                                    │
  Gemini:  function_call() → strict JSON                              │
  Output:  AnalysisResult (Pydantic validated)                        │
           ├── primary_hotspot: str                                   │
           ├── hotspots: list[HotspotDetail]                          │
           ├── behavioral_patterns: list[str]                         │
           ├── quick_win_available: bool                              │
           └── analysis_confidence: "high"|"medium"|"low"             │
     │                                                                │
     ▼                                                                │
STAGE 2: PLANNER AGENT                                                │
  Class:   PlannerAgent  (app/agents/planner_agent.py)                │
  Input:   UserContext + AnalysisResult                               │
  Gemini:  function_call() → strict JSON                              │
  Output:  PlanResult (Pydantic validated)                            │
           ├── strategies: list[ReductionStrategy] (3-5 items)        │
           ├── total_potential_saving_kg: float                       │
           ├── recommended_goal_pct: float                            │
           └── thirty_day_focus: str                                  │
     │                                                                │
     ▼                                                                │
STAGE 3: COACH AGENT                                  ◄───────────────┘
  Class:   CoachAgent  (app/agents/coach_agent.py)
  Input:   UserContext + AnalysisResult + PlanResult
  Gemini:  stream_generate() → yields text tokens
  Output:  AsyncGenerator[str]
     │
     ▼ SSE frames: "data: {token}\n\n"
  Frontend useStream() receives tokens → appends to display
     │
     ▼ "data: [PIPELINE_COMPLETE]\n\n"
  Frontend: queryClient.invalidateQueries(['insights'])
```

### Minimal Context Principle

| Agent | Receives | Does NOT Receive |
|---|---|---|
| Baseline Agent | User profile (lifestyle, transport, food, energy) | Activities, prior insights |
| Analyst Agent | Activities (30 days), footprint summary, baseline | Goal detail, prior plan |
| Planner Agent | AnalysisResult, user profile, active goal | Raw activities, baseline detail |
| Coach Agent | AnalysisResult, PlanResult, progress % vs baseline | Raw activities, baseline detail |

---

## 6. Data Flow Diagrams

### 6.1 Onboarding Flow

```
User completes Step 4 (energy habits)
            │
            ▼
POST /api/v1/users ─────────────────────→  INSERT INTO users → return user_id
            │
            ▼
setUserId(user_id) [localStorage]
            │
            ▼
POST /api/v1/onboarding/baseline ───────→  BaselineAgent.estimate(profile)
            │                                        │
            │                                        ▼ Gemini function call
            │                              BaselineResult (Pydantic validated)
            │                                        │
            │                           UPDATE users SET baseline_footprint_kg
            ▼                                        │
  return BaselineResult  ◄───────────────────────────┘
            │
            ▼
navigate('/dashboard')
```

### 6.2 Activity Logging (Natural Language Path)

```
User types: "I drove 25km to the office in my diesel car"
            │
            ▼
POST /api/v1/activities/parse-nl
            │
            ▼
GeminiService.function_call(NL_PARSE_SCHEMA, description)
            │
            ▼ Gemini returns:
{ category: "transport", type: "car_diesel", amount: 25.0, unit: "km" }
            │
            ▼
CarbonEngine.calculate_activity_co2("transport", "car_diesel", 25.0) → 4.25 kg
            │
            ▼
INSERT INTO activities (user_id, category, type, amount, unit, co2_kg, source='natural_language')
            │
            ▼
UPDATE insights_cache SET is_valid = 0 WHERE user_id = ?   ← cache invalidation
            │
            ▼
return { parsed: {...}, activity_id: 43, co2_kg: 4.25 }
            │
            ▼
React Query: invalidateQueries(['activities', userId])
             invalidateQueries(['carbon', 'summary', userId])
```

### 6.3 Agent Analysis Flow

```
User clicks "Analyze My Footprint"
            │
            ▼
POST /api/v1/agents/analyze → StreamingResponse(event_generator())
            │
            ▼ [AgentOrchestrator]
Check insights_cache for (user_id, 'analyst') → MISS
            │
            ▼
AnalystAgent.analyze(context)
  → GeminiService.function_call() → Gemini API
  → response parsed to AnalysisResult (Pydantic)
  → saved to insights_cache (valid_until = now + 24h)
            │
            ▼
PlannerAgent.plan(context, analysis)
  → GeminiService.function_call() → Gemini API
  → response parsed to PlanResult (Pydantic)
  → saved to insights_cache
            │
            ▼
CoachAgent.coach_stream(context, analysis, plan)
  → GeminiService.stream_generate() → Gemini API (streaming)
  → yields tokens one by one
            │
            ▼ SSE frames: "data: {token}\n\n"
  Frontend useStream() receives tokens
  → appends to content state
  → React re-renders each token
  → "data: [PIPELINE_COMPLETE]\n\n"
  Frontend: queryClient.invalidateQueries(['insights'])
```

---

## 7. Communication Protocols

| Protocol | Usage | Format | Implementation |
|----------|-------|--------|----------------|
| **REST** | All CRUD endpoints | `application/json` request/response | FastAPI routes, `fetch()` client |
| **SSE** | Coach Agent streaming, chat streaming | `text/event-stream`, `data: {payload}\n\n` frames | FastAPI `StreamingResponse`, `useStream` hook |
| **Function Calling** | Baseline, Analyst, Planner agents; NL parsing | Gemini SDK function declarations + `mode: "ANY"` | `GeminiService.function_call()` |
| **File I/O** | Database access | `aiosqlite` async API | `database.py` → SQLite file on disk |

### SSE Frame Format

```
data: Transportation is your largest emission source.\n\n
data: Based on your 80 km weekly commute...\n\n
data: [PIPELINE_COMPLETE]\n\n
```

Error frame: `data: [ERROR] An error occurred. Please try again.\n\n`

---

## 8. Error Propagation Model

```
┌─────────────┐    ┌───────────────────┐    ┌─────────────────┐    ┌──────────────┐
│ Gemini API  │───▶│ Agent Layer       │───▶│ Service Layer   │───▶│ API Layer    │
│ (raw error) │    │ catches + wraps   │    │ logs detail     │    │ shapes JSON  │
│             │    │ → GeminiError     │    │ re-raises typed │    │ → {"detail"} │
└─────────────┘    └───────────────────┘    └─────────────────┘    └──────┬───────┘
                                                                          │
                                                                          ▼
                                                                   ┌──────────────┐
                                                                   │ Frontend     │
                                                                   │ shows safe   │
                                                                   │ error message│
                                                                   └──────────────┘
```

**Rules:**
1. Raw Gemini error text is logged server-side only (log_detail)
2. User-facing message is always safe (user_message)
3. HTTP status codes: 422 (validation), 429 (rate limit), 500 (server/Gemini)
4. SSE error frame: `data: [ERROR] {safe message}\n\n`

---

## 9. Caching Architecture

### 9.1 Client-Side Cache (React Query)

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,     // 5 minutes
      refetchOnWindowFocus: true,     // fresh data when user returns to tab
    },
  },
});
```

Mutation callbacks trigger `queryClient.invalidateQueries()` to synchronize after writes (e.g., logging an activity invalidates `['activities']` and `['carbon', 'summary']`).

### 9.2 Server-Side Cache (SQLite insights_cache)

```python
async def is_valid(user_id: str, agent_type: str) -> bool:
    row = await db.fetchone(
        """SELECT valid_until, is_valid FROM insights_cache
           WHERE user_id = ? AND agent_type = ?
           ORDER BY generated_at DESC LIMIT 1""",
        (user_id, agent_type)
    )
    if not row: return False
    if not row["is_valid"]: return False           # invalidated by new activity
    if row["valid_until"] < datetime.utcnow(): return False  # TTL expired
    return True
```

**Invalidation trigger:** Every `POST /activities` and `POST /activities/parse-nl`:

```sql
UPDATE insights_cache SET is_valid = 0 WHERE user_id = ?
```

### 9.3 Cache Flow Summary

| Event | Client Cache | Server Cache |
|-------|-------------|-------------|
| Activity logged | `invalidateQueries(['activities', 'carbon'])` | `UPDATE insights_cache SET is_valid = 0` |
| Analysis triggered (cache miss) | — | Run full pipeline; store results with `valid_until = now + 24h` |
| Analysis triggered (cache hit) | — | Skip Analyst + Planner; run Coach from cached data |
| Window focus | React Query auto-refetches stale queries | — |

---

*Document ends.*
