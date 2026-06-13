# CarbonSense AI — Architecture Document

**Version:** 1.0  
**Author:** Sovan Bhakta  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3

---

## Table of Contents

1. [Architectural Principles](#1-architectural-principles)
2. [System Context (C4 Level 1)](#2-system-context-c4-level-1)
3. [Container Architecture (C4 Level 2)](#3-container-architecture-c4-level-2)
4. [Frontend Architecture](#4-frontend-architecture)
5. [Backend Architecture](#5-backend-architecture)
6. [Multi-Agent Architecture](#6-multi-agent-architecture)
7. [Data Flow Architecture](#7-data-flow-architecture)
8. [Cross-Cutting Concerns](#8-cross-cutting-concerns)
9. [Deployment Topology](#9-deployment-topology)
10. [Architecture Decision Records](#10-architecture-decision-records)

---

## 1. Architectural Principles

Four principles govern every structural decision in CarbonSense AI:

### 1.1 AI-First, Not AI-Bolted-On
AI reasoning is the core product mechanism — not a peripheral feature. The multi-agent pipeline (Baseline → Analyst → Planner → Coach) is the primary value delivery path. Every meaningful user interaction flows through AI reasoning. This is an AI coaching platform that happens to have a calculator, not a calculator with a chatbot added.

### 1.2 Determinism at the Calculation Layer
Carbon calculations are completely AI-free. The Carbon Engine uses hardcoded, peer-reviewed emission factors with inline citations. This separates *measurement* (deterministic, auditable) from *reasoning* (AI-driven, contextual). A user can trust the numbers independently of whether they trust the AI coaching. This architectural separation also makes the engine independently testable with exact assertions.

### 1.3 Minimum Sufficient Infrastructure
Every infrastructure choice is the simplest option that satisfies the requirement:
- SQLite instead of Postgres: no external DB server required
- No Redis: insight caching in SQLite with a `valid_until` timestamp
- No Auth: session UUID in localStorage eliminates the auth layer entirely
- No LangGraph: custom orchestrator eliminates framework overhead
- SSE instead of WebSocket: one-directional streaming has no need for a full-duplex channel

Complexity is introduced only when a simpler option fails to meet the need.

### 1.4 Score-Aware Architecture
The five competition evaluation criteria are treated as first-class architectural constraints:

| Criterion | Architectural Response |
|-----------|----------------------|
| Code Quality | Layered architecture with single-responsibility modules; TypeScript strict mode; Pydantic v2 |
| Security | Secrets in env only; CORS allowlist; rate limiting middleware; Pydantic input validation |
| Efficiency | Gemini 1.5 Flash; SQLite; async throughout; 24hr insight cache; React Query client cache |
| Testing | Carbon Engine fully unit-testable (zero AI dependency); API integration tests; Vitest frontend |
| Accessibility | shadcn/ui base components; ARIA on all interactive elements; WCAG 2.1 AA target |

---

## 2. System Context (C4 Level 1)

```
╔═══════════════════════════════════════════════════════════════════╗
║                        SYSTEM CONTEXT                             ║
╚═══════════════════════════════════════════════════════════════════╝

  ┌─────────────┐
  │    User     │  A climate-conscious individual on a desktop
  │  (Browser)  │  or mobile web browser
  └──────┬──────┘
         │ HTTPS
         │ REST + SSE (text/event-stream)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CARBONSENSE AI                              │
│                                                                   │
│  An AI-powered sustainability coaching platform that helps        │
│  individuals understand, track, and reduce their carbon           │
│  footprint through multi-agent reasoning and personalized         │
│  coaching — not generic calculators.                              │
└──────────────────────────────┬──────────────────────────────────┘
                                │
               ┌────────────────┴───────────────┐
               │                                 │
               ▼                                 ▼
    ┌────────────────────┐           ┌───────────────────────┐
    │  Google Gemini     │           │  SQLite (on Render)   │
    │  1.5 Flash API     │           │                        │
    │                    │           │  Persistent on-disk   │
    │  Function calling  │           │  user data, activity  │
    │  Streaming SSE     │           │  logs, insight cache  │
    │  Standard gen      │           │  missions, goals      │
    └────────────────────┘           └───────────────────────┘
```

### External Actors and Systems

| Actor/System | Role | Interaction |
|---|---|---|
| User | Climate-conscious individual using the platform | Browser: HTTPS REST + SSE |
| Google Gemini 1.5 Flash | AI reasoning engine for all agents and NL parsing | Server-to-server HTTPS API |
| SQLite (Render disk) | Persistent data store | Local file I/O via aiosqlite |
| Vercel CDN | Static asset delivery for React app | Build-time deploy; zero runtime coupling |
| Render | Hosts the FastAPI process and SQLite file | Platform deployment |

---

## 3. Container Architecture (C4 Level 2)

```
╔═════════════════════════════════════════════════════════════════════════╗
║                         CONTAINER VIEW                                  ║
╚═════════════════════════════════════════════════════════════════════════╝

  User Browser
  ┌──────────────────────────────────────────────────────────────┐
  │                 Single-Page Application                       │
  │           React 18 + TypeScript + Vite (on Vercel)           │
  │                                                               │
  │  Responsibilities:                                            │
  │  · Render all UI (Onboarding, Dashboard, Chat, Log, Missions) │
  │  · Manage session UUID in localStorage                        │
  │  · Stream SSE responses to chat and agent UI                  │
  │  · Keepalive ping every 14 minutes                            │
  │  · Cache server state with React Query                        │
  └───────────────────────────┬──────────────────────────────────┘
                               │ HTTPS REST (JSON)
                               │ HTTPS SSE (text/event-stream)
                               ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                    API + Business Layer                        │
  │              FastAPI Python 3.11 (on Render)                  │
  │                                                               │
  │  Responsibilities:                                            │
  │  · Serve all REST API endpoints under /api/v1                 │
  │  · Orchestrate the multi-agent pipeline                       │
  │  · Apply CORS, rate limiting, input validation                │
  │  · Own all Gemini API calls via GeminiService                 │
  │  · Calculate carbon via CarbonEngine (deterministic)          │
  │  · Read/write all data via SQLite                             │
  └──────────┬────────────────────────────┬──────────────────────┘
             │                            │
             ▼                            ▼
  ┌──────────────────┐          ┌────────────────────┐
  │   SQLite DB      │          │  Gemini 1.5 Flash  │
  │  (Render disk)   │          │  (Google AI API)   │
  │                  │          │                    │
  │  · users         │          │  · Function call   │
  │  · activities    │          │  · Streaming gen   │
  │  · insights_cache│          │  · Standard gen    │
  │  · missions      │          └────────────────────┘
  │  · goals         │
  └──────────────────┘
```

### Container Communication Protocols

| From | To | Protocol | Format |
|---|---|---|---|
| Browser | FastAPI | HTTPS | JSON body / query params |
| Browser | FastAPI (streaming) | HTTPS SSE | `text/event-stream` |
| Browser | FastAPI (keepalive) | HTTPS GET | No body; expects `{"status":"ok"}` |
| FastAPI | Gemini API | HTTPS | Gemini SDK (JSON over HTTP/2) |
| FastAPI | SQLite | File I/O | aiosqlite async API |

---

## 4. Frontend Architecture

### 4.1 Application Shell

```
App.tsx (root)
├── useKeepalive()          ← starts 14-min ping on mount
├── Router (React Router v6)
│   ├── /                  → LandingPage
│   ├── /onboarding        → OnboardingFlow   (redirects to /dashboard if session exists)
│   ├── /dashboard         → DashboardPage    (protected: redirect to /onboarding if no session)
│   ├── /chat              → ChatPage         (protected)
│   ├── /log               → LogPage          (protected)
│   └── /missions          → MissionsPage     (protected)
└── Layout.tsx             ← nav header with EcoPointsBadge, wraps all protected routes
```

### 4.2 Component Responsibility Matrix

| Component | Owns State | Calls API | Renders |
|---|---|---|---|
| `OnboardingFlow` | Step index, form data | `api.users.create`, `api.onboarding.baseline` | 4-step wizard |
| `ActivityLogger` | Tab selection (form/NL) | `api.activities.log`, `api.activities.parseNL` | Dual-mode input form |
| `Dashboard` | Time range selector | `useCarbon()` hook | All 5 metric widgets |
| `FootprintPieChart` | None (display only) | None | Recharts PieChart |
| `TrendLineChart` | None (display only) | None | Recharts LineChart |
| `ChatInterface` | Message history | `useStream('/chat/stream')` | Chat UI + SSE renderer |
| `MissionCenter` | Mission list | `useMissions()` hook | Mission cards |
| `MissionCard` | Acceptance state | `api.missions.accept/complete` | Individual mission |
| `EcoPointsBadge` | None (display only) | `useEcoPoints()` hook | Points + tier label |

### 4.3 State Architecture

**Two distinct state domains — never mixed:**

```
Server State (React Query)          Local State (useState / useReducer)
─────────────────────────────       ────────────────────────────────────
Carbon summary & trends             Onboarding current step
Activity history                    Chat message draft
Active missions                     Activity form fields
User profile                        NL input text
Eco points balance                  Dashboard time range selection
                                    Streaming content buffer
```

React Query manages all server state with:
- `staleTime: 5 * 60 * 1000` (5 minutes — prevents redundant refetches during a session)
- `refetchOnWindowFocus: true` (ensures fresh data when user returns to tab)
- Mutation callbacks call `queryClient.invalidateQueries()` to synchronize after writes

### 4.4 Routing Guard Pattern

```typescript
// components/ProtectedRoute.tsx
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  useEffect(() => {
    if (!hasSession()) navigate('/onboarding', { replace: true });
  }, [navigate]);
  return hasSession() ? <>{children}</> : null;
}
```

All routes under `/dashboard`, `/chat`, `/log`, and `/missions` are wrapped in `ProtectedRoute`. If no UUID exists in localStorage, the user is redirected to onboarding. This is the entire "auth" system for the MVP.

---

## 5. Backend Architecture

### 5.1 Layer Model

```
┌──────────────────────────────────────────────┐
│           API Layer (api/v1/*.py)             │
│   HTTP concerns: routing, validation, SSE,    │
│   rate limiting, error shaping                │
├──────────────────────────────────────────────┤
│        Service Layer (services/*.py)          │
│   Business logic: orchestration, caching,     │
│   carbon math, Gemini integration             │
├──────────────────────────────────────────────┤
│          Agent Layer (agents/*.py)            │
│   AI reasoning: each agent is a standalone    │
│   class owning its schema + system prompt     │
├──────────────────────────────────────────────┤
│         Domain Layer (models/*.py)            │
│   Pydantic schemas for every contract         │
│   between layers (never raw dicts)            │
├──────────────────────────────────────────────┤
│     Infrastructure Layer (db/*.py)            │
│   Database connection, migration runner,      │
│   raw SQL query helpers                       │
└──────────────────────────────────────────────┘
```

### 5.2 Layer Communication Rules

| From Layer | Can Call | Cannot Call |
|---|---|---|
| API Layer | Service Layer, Domain Layer | Agent Layer directly, Infrastructure Layer |
| Service Layer | Agent Layer, Domain Layer, Infrastructure Layer | API Layer |
| Agent Layer | GeminiService (Service), Domain Layer | Database directly, API Layer |
| Domain Layer | Nothing (pure data models) | Any layer |
| Infrastructure Layer | Nothing upward | — |

This ensures that the API layer never directly calls Gemini or the database, and that agents never access the database — they receive all context they need from the orchestrator.

### 5.3 Error Handling Architecture

All errors are caught at the API layer and shaped into a consistent response envelope. Raw exception text never reaches the frontend.

```python
# Domain: safe error types
class CarbonSenseError(Exception):
    def __init__(self, user_message: str, log_detail: str):
        self.user_message = user_message
        self.log_detail = log_detail

class GeminiError(CarbonSenseError): pass
class ValidationError(CarbonSenseError): pass
class RateLimitError(CarbonSenseError): pass

# API layer: global exception handler
@app.exception_handler(CarbonSenseError)
async def carbon_sense_error_handler(request, exc: CarbonSenseError):
    logger.error(f"[{type(exc).__name__}] {exc.log_detail}")
    return JSONResponse(
        status_code=422 if isinstance(exc, ValidationError) else 500,
        content={"detail": exc.user_message}
    )
```

---

## 6. Multi-Agent Architecture

### 6.1 Pipeline Overview

```
User triggers analysis
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATOR                            │
│                  AgentOrchestrator.run_pipeline()                │
└───┬──────────────────────────────────────────────────────────┬──┘
    │                                                           │
    │ 1. Check insight cache                                    │
    │    ├── HIT: skip Stage 1+2, go straight to Stage 3       │
    │    └── MISS: run full pipeline                            │
    │                                                           │
    ▼                                                           │
STAGE 1: ANALYST AGENT                                         │
  Input:  UserContext (activities, footprint, profile)         │
  Output: AnalysisResult (validated Pydantic)                  │
  Gemini: function calling → strict JSON                       │
    │                                                           │
    ▼                                                           │
STAGE 2: PLANNER AGENT                                         │
  Input:  UserContext + AnalysisResult                         │
  Output: PlanResult (validated Pydantic)                      │
  Gemini: function calling → strict JSON                       │
    │                                                           │
    ▼                                                           │
STAGE 3: COACH AGENT                             ◄─────────────┘
  Input:  UserContext + AnalysisResult + PlanResult
  Output: AsyncGenerator[str] (streaming tokens)
  Gemini: standard streaming generation
    │
    ▼
  SSE stream → Frontend
```

### 6.2 Agent Contract Definitions

Each agent is a class that exposes exactly one public method. Its inputs and outputs are typed Pydantic models. No agent receives more context than it needs.

```
BaselineAgent
  Method: async estimate(profile: UserProfile) → BaselineResult
  Gemini: function calling

AnalystAgent
  Method: async analyze(context: UserContext) → AnalysisResult
  Gemini: function calling

PlannerAgent
  Method: async plan(context: UserContext, analysis: AnalysisResult) → PlanResult
  Gemini: function calling

CoachAgent
  Method: async coach_stream(context, analysis, plan) → AsyncGenerator[str]
  Gemini: streaming standard generation
```

### 6.3 Minimal Context Principle

Each agent receives only the subset of user context it needs:

| Agent | Receives | Does NOT Receive |
|---|---|---|
| Baseline Agent | User profile (lifestyle, transport, food, energy habits) | Activities, prior insights |
| Analyst Agent | Activity history (30 days), footprint summary, baseline | Goal detail, prior plan |
| Planner Agent | AnalysisResult, user profile, active goal | Raw activities, baseline detail |
| Coach Agent | AnalysisResult, PlanResult, progress % vs baseline | Raw activities, baseline detail |

This prevents context bloat (reducing token cost) and forces each agent to reason only from relevant information.

### 6.4 Typed Agent Communication

Agents communicate via Pydantic models serialized as JSON. No agent passes raw strings or dicts to the next stage.

```
AnalysisResult
├── primary_hotspot: str
├── hotspots: list[HotspotDetail]
│   └── HotspotDetail
│       ├── category: str
│       ├── pct_of_total: float
│       ├── vs_baseline_change_pct: float
│       ├── key_behaviors: list[str]       ← max 3
│       └── reduction_opportunity_kg: float
├── behavioral_patterns: list[str]         ← max 3
├── quick_win_available: bool
└── analysis_confidence: "high" | "medium" | "low"

PlanResult
├── strategies: list[ReductionStrategy]    ← 3-5 items
│   └── ReductionStrategy
│       ├── title: str
│       ├── action: str
│       ├── category: str
│       ├── monthly_saving_kg: float
│       ├── difficulty: "easy" | "medium" | "hard"
│       ├── timeframe_days: int
│       └── mission_type: str | None
├── total_potential_saving_kg: float
├── recommended_goal_pct: float
└── thirty_day_focus: str
```

### 6.5 Cache Invalidation Architecture

The insight cache uses a two-condition validity check:

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

**Invalidation trigger:** Every `POST /activities` and `POST /activities/parse-nl` executes:
```sql
UPDATE insights_cache SET is_valid = 0 WHERE user_id = ?
```

This ensures that after any new activity is logged, the next analysis request runs a fresh pipeline rather than serving stale insights.

---

## 7. Data Flow Architecture

### 7.1 Onboarding Flow

```
User completes Step 4 (energy habits)
            │
            ▼
POST /users  ──────────────────────→  INSERT users row  →  return user_id
            │
            ▼
setUserId(user_id) [localStorage]
            │
            ▼
POST /onboarding/baseline ──────────→  BaselineAgent.estimate(profile)
            │                                    │
            │                                    ▼ Gemini function call
            │                          BaselineResult (validated)
            │                                    │
            │                         UPDATE users SET baseline_footprint_kg
            ▼                                    │
  return BaselineResult  ◄───────────────────────┘
            │
            ▼
navigate('/dashboard')
```

### 7.2 Activity Logging (Natural Language Path)

```
User types: "I drove 25km to the office this morning in my diesel car"
            │
            ▼
POST /activities/parse-nl
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
INSERT activities (user_id, category, type, amount, unit, co2_kg, source='natural_language')
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

### 7.3 Agent Pipeline + Streaming Flow

```
User clicks "Analyze My Footprint"
            │
            ▼
POST /agents/analyze → StreamingResponse(event_generator())
            │
            ▼ [Orchestrator]
Check insights_cache for (user_id, 'analyst') → MISS
            │
            ▼
AnalystAgent.analyze(context)
  → GeminiService.function_call() ──→ Gemini API
  → response parsed to AnalysisResult
  → saved to insights_cache (valid_until = now + 24h)
            │
            ▼
PlannerAgent.plan(context, analysis)
  → GeminiService.function_call() ──→ Gemini API
  → response parsed to PlanResult
  → saved to insights_cache
            │
            ▼
CoachAgent.coach_stream(context, analysis, plan)
  → GeminiService.stream_generate() ──→ Gemini API (streaming)
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

## 8. Cross-Cutting Concerns

### 8.1 Logging Architecture

```python
# Structured logging, JSON format in production
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })

# Log levels by layer:
# API layer:     INFO for all requests (method, path, status, duration_ms)
# Service layer: DEBUG for cache hits/misses, INFO for agent pipeline stages
# Agent layer:   INFO for Gemini call start/complete, WARNING for validation failures
# Infrastructure: DEBUG for SQL queries in development
```

**What is never logged:**
- Gemini API key or any `.env` value
- Raw user activity data (only activity IDs and categories)
- SSE token content

### 8.2 Rate Limiting Architecture

```python
# middleware/rate_limiter.py
# Simple in-memory sliding window — sufficient for single-user MVP
from collections import defaultdict, deque
from time import time

class RateLimiter:
    def __init__(self):
        self.windows: dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time()
        window = self.windows[key]
        # Remove expired timestamps
        while window and window[0] < now - window_seconds:
            window.popleft()
        if len(window) >= limit:
            return False
        window.append(now)
        return True

rate_limiter = RateLimiter()

# Usage in endpoint:
# if not rate_limiter.is_allowed(f"{user_id}:analyze", limit=3, window_seconds=3600):
#     raise RateLimitError("Too many analysis requests. Please wait before retrying.")
```

### 8.3 Accessibility Architecture

All UI components follow three rules:

**Rule 1: Every interactive element has a visible label and ARIA label**
```tsx
<Button
  onClick={handleAnalyze}
  aria-label="Analyze my carbon footprint"
  disabled={isStreaming}
>
  Analyze
</Button>
```

**Rule 2: All charts have text alternatives**
```tsx
<PieChart aria-label="Carbon footprint breakdown by category">
  <title>Carbon breakdown: Transport 48%, Energy 25%, Food 19%, Shopping 8%</title>
  ...
</PieChart>
```

**Rule 3: Focus management on navigation**
After route changes, focus is moved to the main heading of the new page via `useEffect(() => { headingRef.current?.focus(); }, [])`.

---

## 9. Deployment Topology

```
╔══════════════════════════════════════════════════════════════════════╗
║                      PRODUCTION TOPOLOGY                             ║
╚══════════════════════════════════════════════════════════════════════╝

Developer Workstation
  └── git push origin main
             │
             ├──────────────────────────────────┐
             ▼                                  ▼
    ┌──────────────────┐              ┌────────────────────┐
    │  Vercel           │              │  Render             │
    │  (Frontend)       │              │  (Backend)          │
    │                   │              │                     │
    │  Trigger: push    │              │  Trigger: push      │
    │  Build: vite build│              │  Build: pip install │
    │  Output: CDN edge │              │  Start: uvicorn     │
    │                   │              │  Health: /health    │
    │  URL: *.vercel.app│              │  URL: *.onrender.com│
    └────────┬──────────┘              └──────────┬──────────┘
             │ HTTPS                               │
             │ serves index.html                   │ HTTPS REST + SSE
             ▼                                     ▼
    ┌──────────────────┐              ┌────────────────────┐
    │  User Browser     │──────────────►  FastAPI Process  │
    │                   │              │                     │
    │  · React SPA      │              │  SQLite DB         │
    │  · localStorage   │              │  (persistent disk) │
    │  · Keepalive ping │              │                     │
    └──────────────────┘              │  Gemini API calls   │
                                      │  (outbound HTTPS)   │
                                      └─────────┬───────────┘
                                                │ HTTPS
                                                ▼
                                      ┌────────────────────┐
                                      │  Google Gemini API  │
                                      │  1.5 Flash          │
                                      └────────────────────┘
```

### 9.1 Render Free Tier Constraints

| Constraint | Impact | Mitigation |
|---|---|---|
| Spins down after 15min inactivity | Cold start delay on first request | 14-min keepalive ping from frontend |
| 512 MB RAM | Limits concurrent requests | Async FastAPI + SQLite (low memory) |
| Ephemeral disk on redeploy | SQLite data lost on new deploy | Acceptable for competition scope; V2 uses persistent volume |
| Shared CPU | Slower Gemini API latency | Mitigated by streaming (first token fast) |

### 9.2 CI/CD Pipeline

```
git push origin main
         │
         ▼
GitHub Actions (ci.yml)
  ├── backend-test job
  │     ├── pip install requirements.txt
  │     ├── pytest tests/ -v --cov=app
  │     └── fail on coverage < 70%
  │
  └── frontend-test job
        ├── npm ci
        ├── npm run test:run (Vitest)
        └── npm run build (vite build — catches TS errors)
         │
         │ (both jobs pass)
         ▼
Vercel: auto-deploy frontend ← connected to GitHub repo
Render: auto-deploy backend  ← connected to GitHub repo
```

---

## 10. Architecture Decision Records

### ADR-001: Custom Agent Orchestrator vs LangGraph

**Status:** Decided  
**Decision:** Build a custom sequential orchestrator without LangGraph  

**Context:** A multi-agent pipeline could be built with LangGraph, which would provide state graphs, checkpointing, and human-in-the-loop features. However, the pipeline in CarbonSense AI is linear (A→B→C), not cyclic, and has no need for graph-based state management.

**Consequences:**
- Positive: Zero framework overhead; lighter dependency list; cleaner, more readable code that evaluating AI can understand without framework knowledge
- Positive: The orchestrator is fully testable with direct unit tests
- Negative: No built-in checkpointing or retry logic (acceptable for MVP scope)
- Negative: Adding a cyclic agent loop in V2 requires refactoring

---

### ADR-002: SQLite vs PostgreSQL

**Status:** Decided  
**Decision:** SQLite via aiosqlite

**Context:** The platform is single-user per browser session (UUID-based). No concurrent writes from multiple processes are expected. The platform runs on a single Render instance.

**Consequences:**
- Positive: Zero external infrastructure; the DB is a file on the Render disk
- Positive: Simpler local development (no DB server to start)
- Positive: Dramatically lower complexity for competition scope
- Negative: Data is lost on Render redeployment (ephemeral disk); V2 requires migration to Postgres or a persistent volume mount
- Negative: Not horizontally scalable (acceptable — competition requires a single deployment)

---

### ADR-003: Session UUID vs JWT Authentication

**Status:** Decided  
**Decision:** UUID v4 stored in browser localStorage; no authentication layer

**Context:** The competition evaluates technical implementation of the AI features, not security of user identity management. Building a full auth flow (JWT + refresh tokens + registration + login) would consume 2–3 days and not contribute to the evaluation criteria.

**Consequences:**
- Positive: Eliminates 2–3 days of auth implementation
- Positive: No auth-related attack surface to secure
- Negative: Any user who clears localStorage loses their data (acceptable — competition demo)
- Negative: No multi-device sync (acceptable — competition scope)

---

### ADR-004: SSE vs WebSocket for Streaming

**Status:** Decided  
**Decision:** Server-Sent Events (SSE) over HTTP

**Context:** The streaming use case is one-directional: the server streams Coach Agent tokens to the browser. WebSocket adds full-duplex complexity that is unnecessary for this pattern.

**Consequences:**
- Positive: Simpler server implementation (FastAPI `StreamingResponse` with `text/event-stream`)
- Positive: SSE works natively with Render's free tier (no WebSocket upgrade issues)
- Positive: Automatic reconnection handled by the EventSource API natively
- Negative: Cannot stream user input back to the server simultaneously (not needed for this use case)

---

### ADR-005: Insight Cache in SQLite vs Redis

**Status:** Decided  
**Decision:** Cache agent outputs in the `insights_cache` SQLite table

**Context:** Agent pipeline results (AnalysisResult, PlanResult) are expensive to generate (~8 seconds). They should be cached and reused if the user's activity data has not changed. Redis would provide TTL-based caching out of the box, but adds an external service dependency.

**Consequences:**
- Positive: Cache runs entirely within the existing SQLite connection; zero new infrastructure
- Positive: Cache invalidation on activity log is a simple SQL UPDATE in the same transaction
- Positive: Cache data persists through backend restarts (unlike Redis in-memory)
- Negative: Cache TTL checked in application code rather than automatically by the datastore
- Negative: Slightly more complex than a Redis SET with TTL (acceptable — ~20 lines of Python)

---

*Document ends.*
