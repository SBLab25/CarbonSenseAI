# CarbonSense AI — System Design Document

**Version:** 1.0  
**Author:** Sovan Bhakta  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Component Design](#3-component-design)
4. [Database Design](#4-database-design)
5. [API Design](#5-api-design)
6. [Agent Orchestration Design](#6-agent-orchestration-design)
7. [Security Design](#7-security-design)
8. [Performance & Caching Strategy](#8-performance--caching-strategy)
9. [Deployment Architecture](#9-deployment-architecture)

---

## 1. System Overview

CarbonSense AI is a full-stack AI platform with a React frontend, a FastAPI backend, a custom multi-agent orchestration layer, and a Google Gemini 1.5 Flash integration. The system is organized into six major subsystems that each own a distinct responsibility:

| Subsystem | Responsibility |
|-----------|----------------|
| AI Sustainability Coach | Streaming conversational interface and session orchestration |
| Activity Logger | Dual-input (form + NL) activity collection and carbon computation on save |
| Carbon Engine | Deterministic emission calculation using IPCC/EPA factors |
| Multi-Agent Layer | Sequential pipeline: Baseline → Analyst → Planner → Coach |
| Insights Dashboard | Recharts visualizations of footprint data and trends |
| Mission Center | AI-generated challenges with gamified Eco Points rewards |

All AI reasoning flows through Google Gemini 1.5 Flash. The agent orchestrator is a custom lightweight pipeline — no external framework dependency — using Gemini's function calling API for structured outputs and the standard generation API for streamed Coach Agent responses.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER BROWSER                                │
│                                                                   │
│   React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui        │
│                                                                   │
│  ┌───────────┐ ┌────────────┐ ┌───────────┐ ┌────────────────┐  │
│  │ AI Coach  │ │ Activity   │ │ Dashboard │ │ Mission Center │  │
│  │ (Chat UI) │ │  Logger    │ │(Recharts) │ │  (Eco Points)  │  │
│  └─────┬─────┘ └─────┬──────┘ └─────┬─────┘ └───────┬────────┘  │
│        │             │              │               │             │
│        └─────────────┴──────────────┴───────────────┘            │
│                              │                                    │
│              HTTP REST + SSE (text/event-stream)                  │
│                              │                                    │
│         ┌────────────────────┘                                    │
│         │   Keepalive: GET /health every 14 minutes               │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND (Render)                         │
│                                                                   │
│  ┌──────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐  │
│  │  /chat   │ │/activities │ │ /calculate │ │    /agents     │  │
│  │  (SSE)   │ │   (CRUD)   │ │ (engine)  │ │  (pipeline)    │  │
│  └──────────┘ └────────────┘ └────────────┘ └────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Agent Orchestrator (Custom)                      │ │
│  │   BaselineAgent → AnalystAgent → PlannerAgent → CoachAgent   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Carbon Engine (deterministic)                    │ │
│  │              IPCC / EPA / Poore & Nemecek factors             │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────┬──────────────────┘
                       │                      │
          ┌────────────┘                      └──────────────┐
          ▼                                                   ▼
┌─────────────────┐                             ┌────────────────────┐
│  SQLite on disk │                             │  Gemini 1.5 Flash  │
│                 │                             │  (Google AI Studio) │
│  users          │                             │                    │
│  activities     │                             │  Function Calling  │
│  insights cache │                             │  Streaming SSE     │
│  missions       │                             │  (GenerateContent) │
│  goals          │                             └────────────────────┘
└─────────────────┘
```

### Data Flow Summary

| Flow | Path |
|------|------|
| User chats with coach | Browser → FastAPI `/chat` → GeminiService (stream) → SSE → Browser |
| User logs activity (NL) | Browser → FastAPI `/activities/parse-nl` → GeminiService (function call) → Carbon Engine → SQLite → response |
| User logs activity (form) | Browser → FastAPI `/activities` → Carbon Engine → SQLite → response |
| Analysis triggered | Browser → FastAPI `/agents/analyze` → Orchestrator (Analyst→Planner→Coach) → SSE → Browser |
| Dashboard load | Browser → FastAPI `/carbon/summary` + `/carbon/trends` → SQLite aggregation → JSON response |

---

## 3. Component Design

### 3.1 Frontend Architecture

**Framework:** React 18 + TypeScript (strict mode) + Vite + Tailwind CSS + shadcn/ui

**Routing:** React Router v6 with the following routes:

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `LandingPage` | Intro + CTA for new users |
| `/onboarding` | `OnboardingFlow` | 4-step profile setup |
| `/dashboard` | `Dashboard` | Main analytics view |
| `/chat` | `ChatInterface` | AI coach conversation |
| `/log` | `ActivityLogger` | Log new activities |
| `/missions` | `MissionCenter` | Active + available missions |

**State Management:**  
React Query (TanStack Query) for all server state. `useState` / `useReducer` for local UI state. No global state library — server state is the source of truth.

**Key Custom Hooks:**

| Hook | Responsibility |
|------|----------------|
| `useCarbon()` | Fetch and cache carbon summary + trends |
| `useActivities()` | CRUD operations on activity log |
| `useStream()` | Manage SSE connection lifecycle for chat and agent streaming |
| `useKeepalive()` | Initialize the 14-minute backend ping on app mount |
| `useMissions()` | Fetch, accept, and complete missions |
| `useEcoPoints()` | Read points balance; invalidate on mission completion |

**Streaming Pattern:**

```typescript
// hooks/useStream.ts
export function useStream(endpoint: string) {
  const [content, setContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const startStream = useCallback(async (body: object) => {
    setContent('');
    setIsStreaming(true);
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          setContent(prev => prev + line.slice(6));
        }
      }
    }
    setIsStreaming(false);
  }, [endpoint]);

  return { content, isStreaming, startStream };
}
```

---

### 3.2 Backend Architecture

**Framework:** FastAPI (Python 3.11+) with async/await throughout

**Module Structure:**

```
backend/app/
├── main.py                   # FastAPI app factory, CORS, router registration
├── config.py                 # pydantic-settings: all env vars with validation
├── api/
│   ├── v1/
│   │   ├── chat.py           # POST /chat/message, GET /chat/stream (SSE)
│   │   ├── users.py          # POST /users, GET /users/{id}, PUT /users/{id}
│   │   ├── onboarding.py     # POST /onboarding/baseline
│   │   ├── activities.py     # POST/GET/DELETE /activities, POST /activities/parse-nl
│   │   ├── carbon.py         # GET /carbon/summary/{user_id}, GET /carbon/trends/{user_id}
│   │   ├── agents.py         # POST /agents/analyze (triggers full pipeline)
│   │   ├── missions.py       # GET/POST /missions, POST /missions/{id}/complete
│   │   └── health.py         # GET /health (keepalive endpoint)
├── services/
│   ├── gemini_service.py     # All Gemini API calls: stream, function call, generate
│   ├── carbon_engine.py      # Deterministic emission calculations
│   ├── agent_orchestrator.py # Sequential pipeline: runs all 4 agents in order
│   └── insights_cache.py     # 24-hour cache read/write for agent outputs
├── agents/
│   ├── baseline_agent.py     # Onboarding: profile → initial footprint estimate
│   ├── analyst_agent.py      # Activity data → hotspot analysis
│   ├── planner_agent.py      # Analysis → reduction strategies
│   └── coach_agent.py        # Analysis + plan → streamed coaching message
├── models/
│   ├── schemas.py            # All Pydantic request/response models
│   └── db_models.py          # SQLite table definitions via SQLAlchemy Core
├── db/
│   ├── database.py           # Async SQLite connection pool (aiosqlite)
│   └── migrations/           # Schema migration SQL files (numbered)
└── middleware/
    └── rate_limiter.py       # Simple in-memory rate limiter for AI endpoints
```

---

### 3.3 Carbon Engine Design

The Carbon Engine is a pure-Python module with no AI or database dependency. It accepts typed inputs and returns exact float values. All emission factors are declared as named constants with inline source citations.

**Design Principles:**
- Zero AI dependency — fully deterministic and unit-testable
- All factors declared as module-level constants, not magic numbers
- Factor dictionary is the single source of truth for all calculations
- Aggregation functions compose the base calculation function

```python
# services/carbon_engine.py

# Transport factors: kg CO₂ per km
# Source: UK DEFRA Conversion Factors 2023, IPCC AR6
TRANSPORT_FACTORS = {
    "car_petrol":            0.21,
    "car_diesel":            0.17,
    "car_electric":          0.05,
    "bus":                   0.089,
    "train":                 0.041,
    "flight_domestic":       0.255,
    "flight_international":  0.195,
    "motorcycle":            0.114,
    "bicycle":               0.0,
    "walking":               0.0,
}

# Energy factors: kg CO₂ per kWh
# Source: IEA 2023, India CEA grid emission factor
ENERGY_FACTORS = {
    "electricity": 0.708,   # India grid average
    "natural_gas": 0.202,
    "lpg":         0.214,
}

# Food factors: kg CO₂ per kg of food
# Source: Poore & Nemecek (2018), Science
FOOD_FACTORS = {
    "beef":       27.0,
    "lamb":       39.2,
    "pork":       12.1,
    "chicken":     6.9,
    "fish":        6.1,
    "dairy":       3.2,
    "eggs":        4.8,
    "vegetables":  2.0,
    "fruits":      1.1,
    "grains":      1.4,
    "legumes":     0.9,
}

# Shopping factors: kg CO₂ per item
# Source: Berners-Lee, How Bad Are Bananas? (2020)
SHOPPING_FACTORS = {
    "electronics":     70.0,
    "clothing":        10.0,
    "household_item":  15.0,
}

def calculate_activity_co2(category: str, activity_type: str, amount: float) -> float:
    """
    Calculate kg CO₂ for a single activity.
    Returns 0.0 for unknown types rather than raising an exception.
    """
    factors_map = {
        "transport": TRANSPORT_FACTORS,
        "energy":    ENERGY_FACTORS,
        "food":      FOOD_FACTORS,
        "shopping":  SHOPPING_FACTORS,
    }
    factor = factors_map.get(category, {}).get(activity_type, 0.0)
    return round(factor * amount, 4)
```

---

### 3.4 Agent Orchestration Design

The orchestrator is a custom sequential pipeline. Each agent is a standalone class that wraps a Gemini API call and returns a validated Pydantic model. The orchestrator calls them in order, passing typed outputs as inputs to the next stage.

```
AgentOrchestrator.run_pipeline(user_id, context)
        │
        ├── 1. AnalystAgent.analyze(context) → AnalysisResult
        │         └── Gemini function call → validates JSON → AnalysisResult
        │
        ├── 2. PlannerAgent.plan(context, analysis) → PlanResult
        │         └── Gemini function call → validates JSON → PlanResult
        │
        └── 3. CoachAgent.coach(context, analysis, plan) → AsyncGenerator[str]
                  └── Gemini streaming generate → yields text tokens → SSE
```

**Context Object:**

```python
class UserContext(BaseModel):
    user_id: str
    profile: UserProfile
    baseline_footprint: FootprintSummary
    current_footprint: FootprintSummary
    recent_activities: list[ActivityRecord]  # last 30 days
    active_goal: Goal | None
    progress_pct: float  # reduction from baseline
```

**Error Handling Strategy:**  
Each agent call is wrapped in a try/except. If Gemini returns a malformed response or the Pydantic validation fails, the orchestrator returns a `PipelineError` model with a safe user-facing message. The raw Gemini error is logged server-side but never forwarded to the frontend.

---

## 4. Database Design

### 4.1 Technology Choice

SQLite via `aiosqlite` for async operations. Rationale:
- Zero external infrastructure (no Postgres server required)
- Repo-size compliant (database file is not committed; created fresh on deploy)
- Single-user MVP does not require connection pooling
- Performance sufficient for competition scope (< 10,000 rows)

### 4.2 Schema

```sql
-- Session-based identity (UUID generated at onboarding, stored in localStorage)
CREATE TABLE users (
    id              TEXT        PRIMARY KEY,    -- UUID v4
    name            TEXT        NOT NULL,
    country         TEXT,
    city            TEXT,
    lifestyle_type  TEXT,                        -- urban | suburban | rural
    diet_type       TEXT,                        -- vegan | vegetarian | mixed | high_meat
    baseline_footprint_kg  REAL DEFAULT 0.0,    -- monthly kg CO₂ from onboarding
    monthly_target_reduction_pct  REAL DEFAULT 15.0,
    eco_points      INTEGER     DEFAULT 0,
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- Every logged activity (transport, energy, food, shopping)
CREATE TABLE activities (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT        NOT NULL REFERENCES users(id),
    category    TEXT        NOT NULL,   -- transport | energy | food | shopping
    type        TEXT        NOT NULL,   -- e.g. car_petrol, beef, electricity
    amount      REAL        NOT NULL,   -- raw quantity (km, kWh, kg, count)
    unit        TEXT        NOT NULL,   -- km | kWh | kg | item
    co2_kg      REAL        NOT NULL,   -- calculated at time of logging
    source      TEXT        DEFAULT 'form',  -- form | natural_language
    notes       TEXT,
    logged_at   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- Cached agent outputs (invalidated on each new activity log)
CREATE TABLE insights_cache (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT        NOT NULL REFERENCES users(id),
    agent_type      TEXT        NOT NULL,   -- analyst | planner | coach
    content_json    TEXT        NOT NULL,   -- serialized Pydantic model as JSON
    generated_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    valid_until     TIMESTAMP   NOT NULL,   -- generated_at + 24 hours
    is_valid        INTEGER     DEFAULT 1   -- 0 = invalidated by new activity
);

-- Missions generated by Planner Agent
CREATE TABLE missions (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT        NOT NULL REFERENCES users(id),
    title           TEXT        NOT NULL,
    description     TEXT        NOT NULL,
    category        TEXT        NOT NULL,
    target_reduction_kg  REAL,
    eco_points_reward    INTEGER DEFAULT 100,
    status          TEXT        DEFAULT 'pending',  -- pending | active | completed | expired
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    accepted_at     TIMESTAMP,
    completed_at    TIMESTAMP,
    deadline        TIMESTAMP
);

-- User goals (set during or after onboarding)
CREATE TABLE goals (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_id             TEXT        NOT NULL REFERENCES users(id),
    target_reduction_pct  REAL      NOT NULL DEFAULT 15.0,
    baseline_kg         REAL        NOT NULL,
    deadline            TIMESTAMP,
    status              TEXT        DEFAULT 'active',  -- active | achieved | abandoned
    created_at          TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for frequent query patterns
CREATE INDEX idx_activities_user_date ON activities(user_id, logged_at DESC);
CREATE INDEX idx_activities_user_category ON activities(user_id, category);
CREATE INDEX idx_insights_cache_user ON insights_cache(user_id, agent_type, is_valid);
CREATE INDEX idx_missions_user_status ON missions(user_id, status);
```

### 4.3 Key Query Patterns

| Query | Purpose | Optimization |
|-------|---------|--------------|
| Monthly footprint by category | Dashboard Category Breakdown | Covered by `idx_activities_user_date` |
| Daily totals (last 30 days) | Trend chart | DATE group-by on `logged_at` |
| Active missions | Mission Center panel | Covered by `idx_missions_user_status` |
| Valid insight cache check | Before running agent pipeline | Covered by `idx_insights_cache_user` |

---

## 5. API Design

**Base URL:** `https://carbonsense-api.onrender.com/api/v1`  
**Content-Type:** `application/json` for all JSON endpoints; `text/event-stream` for SSE endpoints

### 5.1 Users & Onboarding

```
POST   /users                         Create new user (called at end of onboarding)
GET    /users/{user_id}               Get user profile
PUT    /users/{user_id}               Update user profile
POST   /onboarding/baseline           Run Baseline Agent, return initial footprint
GET    /health                        Health check (keepalive)
```

**POST /users — Request:**
```json
{
  "name": "Alex",
  "country": "India",
  "city": "Bengaluru",
  "lifestyle_type": "urban",
  "diet_type": "mixed",
  "primary_transport": "car_petrol",
  "weekly_transport_km": 80,
  "monthly_electricity_kwh": 150,
  "heating_type": "lpg"
}
```

**POST /users — Response:**
```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-06-09T10:00:00Z"
}
```

**POST /onboarding/baseline — Response:**
```json
{
  "user_id": "a1b2c3d4...",
  "monthly_baseline_kg": 187.4,
  "breakdown": {
    "transport": 95.2,
    "energy": 42.8,
    "food": 38.1,
    "shopping": 11.3
  },
  "vs_india_average_pct": 118
}
```

---

### 5.2 Activities

```
POST   /activities                    Log a new activity (structured form input)
POST   /activities/parse-nl           Parse NL description → structured activity + auto-log
GET    /activities/{user_id}          Get paginated activity history
DELETE /activities/{activity_id}      Delete an activity (recalculates running total)
```

**POST /activities — Request:**
```json
{
  "user_id": "a1b2c3d4...",
  "category": "transport",
  "type": "car_petrol",
  "amount": 20.0,
  "unit": "km",
  "notes": "Morning commute"
}
```

**POST /activities — Response:**
```json
{
  "activity_id": 42,
  "co2_kg": 4.2,
  "category": "transport",
  "logged_at": "2026-06-09T08:30:00Z"
}
```

**POST /activities/parse-nl — Request:**
```json
{
  "user_id": "a1b2c3d4...",
  "description": "I drove 25 km to the office this morning in my diesel car"
}
```

**POST /activities/parse-nl — Response:**
```json
{
  "parsed": {
    "category": "transport",
    "type": "car_diesel",
    "amount": 25.0,
    "unit": "km"
  },
  "activity_id": 43,
  "co2_kg": 4.25,
  "confidence": "high"
}
```

---

### 5.3 Carbon Calculations

```
GET    /carbon/summary/{user_id}      Monthly footprint summary + category breakdown
GET    /carbon/trends/{user_id}?days=30   Daily CO₂ totals for trend chart
GET    /carbon/progress/{user_id}     Progress vs baseline and vs goal
```

**GET /carbon/summary/{user_id} — Response:**
```json
{
  "user_id": "a1b2c3d4...",
  "period": "2026-06",
  "total_kg": 142.3,
  "baseline_kg": 187.4,
  "reduction_pct": 24.1,
  "breakdown": {
    "transport": { "kg": 68.1, "pct": 47.9 },
    "energy":    { "kg": 35.4, "pct": 24.9 },
    "food":      { "kg": 27.2, "pct": 19.1 },
    "shopping":  { "kg": 11.6, "pct": 8.2 }
  },
  "vs_india_average_pct": 89.4
}
```

---

### 5.4 Agent Pipeline

```
POST   /agents/analyze               Run full Analyst → Planner pipeline; stream Coach via SSE
GET    /agents/insights/{user_id}    Return cached latest analysis + plan (no AI call)
```

**POST /agents/analyze — Request:**
```json
{
  "user_id": "a1b2c3d4..."
}
```

**POST /agents/analyze — SSE Response Stream:**
```
data: Transportation is your largest emission source at 47.9% of your total footprint.

data: Based on your 80 km weekly commute, switching 3 of those days to the train

data: could reduce your transport emissions by approximately 14 kg CO₂ per month.

data: [PIPELINE_COMPLETE]
```

The `[PIPELINE_COMPLETE]` sentinel signals the frontend that streaming has finished and the cached insights can now be fetched for display in the Dashboard.

---

### 5.5 Missions

```
GET    /missions/{user_id}            Get all missions (active + pending + completed)
POST   /missions/generate             Generate new mission suggestions from Planner output
PUT    /missions/{mission_id}/accept  Accept a pending mission
POST   /missions/{mission_id}/complete  Mark mission complete, award Eco Points
```

---

### 5.6 Chat

```
POST   /chat/stream                   Send message + stream Coach response (SSE)
```

**POST /chat/stream — Request:**
```json
{
  "user_id": "a1b2c3d4...",
  "message": "Why does meat consumption produce so much carbon?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

---

## 6. Agent Orchestration Design

### 6.1 Baseline Agent

**Trigger:** Called once at onboarding completion.  
**Input:** User profile (lifestyle, transport habits, diet, energy usage).  
**Gemini Mode:** Function calling with a strictly typed schema — returns structured JSON, not prose.

**Function Schema:**
```json
{
  "name": "set_baseline_footprint",
  "description": "Calculate the user's estimated monthly carbon footprint from their lifestyle profile",
  "parameters": {
    "type": "object",
    "properties": {
      "monthly_total_kg": { "type": "number" },
      "transport_kg":     { "type": "number" },
      "energy_kg":        { "type": "number" },
      "food_kg":          { "type": "number" },
      "shopping_kg":      { "type": "number" },
      "primary_hotspot":  { "type": "string" },
      "confidence":       { "type": "string", "enum": ["high", "medium", "low"] }
    },
    "required": ["monthly_total_kg", "transport_kg", "energy_kg", "food_kg", "shopping_kg"]
  }
}
```

**System Prompt Strategy:** The agent is given the user's profile as a structured JSON block within the system prompt, along with authoritative emission factor reference data. This grounds its estimates in real numbers rather than hallucinated values.

---

### 6.2 Carbon Analyst Agent

**Trigger:** Called as Stage 1 of the full pipeline.  
**Input:** `UserContext` (profile, baseline, recent activities, current footprint summary).  
**Gemini Mode:** Function calling → `AnalysisResult` Pydantic model.

**Output Schema:**
```python
class HotspotDetail(BaseModel):
    category: str
    pct_of_total: float
    vs_baseline_change_pct: float
    key_behaviors: list[str]        # max 3 specific behaviors observed
    reduction_opportunity_kg: float  # estimated monthly kg if addressed

class AnalysisResult(BaseModel):
    primary_hotspot: str
    hotspots: list[HotspotDetail]   # sorted by pct_of_total desc
    behavioral_patterns: list[str]  # max 3 observed patterns
    quick_win_available: bool
    analysis_confidence: str        # high | medium | low
```

---

### 6.3 Planner Agent

**Trigger:** Called as Stage 2 of the full pipeline, immediately after Analyst.  
**Input:** `AnalysisResult` + `UserContext`.  
**Gemini Mode:** Function calling → `PlanResult` Pydantic model.

**Output Schema:**
```python
class ReductionStrategy(BaseModel):
    title: str
    action: str                     # specific, actionable description
    category: str
    monthly_saving_kg: float        # estimated CO₂ reduction
    difficulty: str                 # easy | medium | hard
    timeframe_days: int             # how quickly impact is felt
    mission_type: str | None        # suggests a Mission Center challenge

class PlanResult(BaseModel):
    strategies: list[ReductionStrategy]  # 3–5 strategies, ranked by impact
    total_potential_saving_kg: float
    recommended_goal_pct: float     # suggested reduction target (5–30%)
    thirty_day_focus: str           # the single most impactful action
```

---

### 6.4 Coach Agent

**Trigger:** Called as Stage 3 (final stage) of the full pipeline.  
**Input:** `AnalysisResult` + `PlanResult` + user progress percentage.  
**Gemini Mode:** Standard streaming generation (yields text tokens via SSE).

**System Prompt Structure:**
```
You are Alex's personal sustainability coach. You have just completed a full analysis
of their carbon footprint. Your role is to communicate the key findings in a warm,
encouraging, and specific way — not generic advice.

Context provided to you:
- User's primary hotspot: [from AnalysisResult]
- Top 3 reduction strategies: [from PlanResult]
- Progress vs baseline: [X% reduction achieved]

Write a coaching message that:
1. Opens with a specific observation about their footprint (use their real data)
2. Presents the single most impactful action they can take this week
3. Closes with motivation that references their specific progress
4. Mentions the Mission Center to frame it as a concrete challenge

Keep the tone: warm, expert, specific, achievable. Not preachy.
Length: 150–200 words.
```

---

### 6.5 Cache Strategy

| Event | Cache Action |
|-------|-------------|
| New activity logged | Invalidate all insight cache rows for this user_id |
| `/agents/analyze` called | Check cache first; if valid hit, skip Analyst + Planner, run Coach from cached results |
| Coach response generated | Cache Coach output with 24hr TTL |
| Cache miss | Run full pipeline; cache all three outputs |

This means a user who logs activities daily always gets a fresh pipeline run on their first analysis request each day. A user who logs once a week gets their Day 1 insights served from cache for 24 hours, reducing Gemini API costs.

---

## 7. Security Design

### 7.1 Secrets Management

```
# .env (never committed, in .gitignore)
GEMINI_API_KEY=your_key_here
DATABASE_URL=./carbonsense.db
ALLOWED_ORIGINS=https://carbonsense.vercel.app,http://localhost:5173
RATE_LIMIT_AI_RPM=10
```

All environment variables are loaded and validated at startup via `pydantic-settings`. If a required variable is missing, the server refuses to start.

### 7.2 CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,    # explicit list, never "*" in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)
```

### 7.3 Rate Limiting

AI endpoints (`/chat/stream`, `/agents/analyze`, `/activities/parse-nl`) are rate-limited per user_id using a simple in-memory sliding window counter:

- `/agents/analyze`: 3 requests/hour/user
- `/chat/stream`: 10 requests/minute/user  
- `/activities/parse-nl`: 20 requests/minute/user

### 7.4 Input Validation

All request bodies are Pydantic models with explicit field validation:
- String fields: `max_length` constraints
- Numeric fields: `ge=0` and `le=max_value` bounds
- Enum fields: restricted to defined values
- User IDs: validated as UUID format before any database query

### 7.5 Data Exposure

- User UUID is the only identifier stored in the browser (localStorage)
- No PII collected beyond name and location
- Activity data and carbon calculations are never logged to console in production
- Gemini API key is exclusively server-side; the frontend never touches it

---

## 8. Performance & Caching Strategy

| Layer | Strategy | Impact |
|-------|----------|--------|
| Vercel CDN | Static assets (JS, CSS, fonts) served from edge | FCP < 1.5s globally |
| React Query | All API responses cached in-memory with staleTime=5min | Dashboard loads instantly on navigation |
| Insight Cache (SQLite) | 24hr agent output cache per user | 60%+ of analysis calls skip Gemini |
| Gemini Flash | Lowest-latency Gemini tier (avg 600ms first token) | Agent pipeline completes in ~5–8s |
| SQLite aggregation | Monthly totals pre-computed in SQL GROUP BY | Dashboard queries < 50ms |
| SSE streaming | Coach response streamed token-by-token | Perceived latency near-zero |

---

## 9. Deployment Architecture

### 9.1 Frontend (Vercel)

```
GitHub push to main
        ↓
Vercel CI: npm run build (vite build)
        ↓
Static bundle deployed to Vercel CDN
        ↓
Environment variable: VITE_API_URL = https://carbonsense-api.onrender.com
```

### 9.2 Backend (Render)

```
GitHub push to main
        ↓
Render CI: pip install -r requirements.txt
        ↓
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
        ↓
Health check: GET /api/v1/health → 200 OK
```

### 9.3 Render Keepalive

Render's free tier spins down services after 15 minutes of inactivity. A keepalive mechanism is implemented client-side in the React app:

```typescript
// lib/keepalive.ts
const PING_INTERVAL_MS = 14 * 60 * 1000; // 14 minutes

export function startKeepalive(): () => void {
  const ping = () =>
    fetch(`${import.meta.env.VITE_API_URL}/api/v1/health`).catch(() => {});

  ping(); // immediate ping on app load
  const interval = setInterval(ping, PING_INTERVAL_MS);
  return () => clearInterval(interval); // cleanup function for useEffect
}
```

Called in `App.tsx`:
```typescript
useEffect(() => {
  const cleanup = startKeepalive();
  return cleanup;
}, []);
```

### 9.4 Environment Variables Summary

| Variable | Location | Value |
|----------|----------|-------|
| `GEMINI_API_KEY` | Render → Environment | Google AI Studio API key |
| `DATABASE_URL` | Render → Environment | `./carbonsense.db` |
| `ALLOWED_ORIGINS` | Render → Environment | Vercel deployment URL |
| `VITE_API_URL` | Vercel → Environment | Render service URL |

---

*Document ends.*
