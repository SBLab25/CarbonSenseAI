# CarbonSense AI — Monorepo Structure

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. Repository Overview

| Property | Value |
|----------|-------|
| **Purpose** | Full-stack AI sustainability coaching platform for PromptWars Challenge 3 |
| **Size Constraint** | Total repo ≤ 10 MB (excluding `.gitignore`'d files) |
| **Branch Strategy** | Single branch: `main` (competition rule) |
| **Visibility** | Public GitHub repository |
| **Packages** | Two main packages: `frontend/` and `backend/` |

---

## 2. Full Annotated Directory Tree

```
carbonsense-ai/                            ← Root of public GitHub repo
│
├── .github/
│   └── workflows/
│       └── ci.yml                         ← GitHub Actions: lint + test on push to main
│
├── frontend/                              ← React SPA (deployed to Vercel)
│   ├── public/
│   │   └── favicon.svg                    ← App favicon
│   ├── src/
│   │   ├── components/                    ← UI components (PascalCase filenames)
│   │   │   ├── ui/                        ← shadcn/ui base components (Button, Card, Input, etc.)
│   │   │   ├── ChatInterface.tsx          ← Streaming chat with AI Coach (SSE display)
│   │   │   ├── ActivityLogger.tsx         ← Dual-mode input: form + natural language tabs
│   │   │   ├── ActivityForm.tsx           ← Structured form for activity logging
│   │   │   ├── NLActivityInput.tsx        ← Natural language input with Gemini parsing
│   │   │   ├── Dashboard.tsx              ← Main analytics panel with 6 widgets
│   │   │   ├── FootprintPieChart.tsx      ← Recharts PieChart: category breakdown
│   │   │   ├── TrendLineChart.tsx         ← Recharts LineChart: daily CO₂ trend
│   │   │   ├── GoalProgressBar.tsx        ← Progress bar: reduction % vs target %
│   │   │   ├── MissionCenter.tsx          ← Mission panels: available, active, completed
│   │   │   ├── MissionCard.tsx            ← Individual mission card with accept/complete
│   │   │   ├── EcoPointsBadge.tsx         ← Points balance + tier label in nav header
│   │   │   ├── OnboardingFlow.tsx         ← 4-step onboarding wizard
│   │   │   └── Layout.tsx                 ← App shell: nav header + <Outlet /> wrapper
│   │   ├── hooks/                         ← Custom React hooks (camelCase filenames)
│   │   │   ├── useCarbon.ts               ← Fetch/cache carbon summary + trends (React Query)
│   │   │   ├── useActivities.ts           ← CRUD operations on activity log
│   │   │   ├── useStream.ts               ← SSE streaming connection lifecycle
│   │   │   ├── useMissions.ts             ← Fetch, accept, complete missions
│   │   │   ├── useUser.ts                 ← Fetch user profile + session management
│   │   │   └── useKeepalive.ts            ← 14-min backend ping (prevents Render spin-down)
│   │   ├── lib/                           ← Utilities (camelCase filenames)
│   │   │   ├── api.ts                     ← Typed API client (all fetch calls centralized)
│   │   │   ├── keepalive.ts               ← startKeepalive() — 14-min interval ping
│   │   │   ├── user-session.ts            ← localStorage UUID management (get/set/clear/has)
│   │   │   └── utils.ts                   ← Formatters (CO₂ display, dates), helpers
│   │   ├── pages/                         ← Route page components (PascalCase filenames)
│   │   │   ├── Landing.tsx                ← Hero section + feature highlights + CTA
│   │   │   ├── Onboarding.tsx             ← Wraps OnboardingFlow component
│   │   │   ├── DashboardPage.tsx          ← Wraps Dashboard component with data loading
│   │   │   ├── ChatPage.tsx               ← Wraps ChatInterface component
│   │   │   ├── LogPage.tsx                ← Wraps ActivityLogger component
│   │   │   └── MissionsPage.tsx           ← Wraps MissionCenter component
│   │   ├── types/
│   │   │   └── api.ts                     ← TypeScript interfaces mirroring backend Pydantic models
│   │   ├── App.tsx                        ← Root: Router + QueryClientProvider + useKeepalive
│   │   ├── main.tsx                       ← React entrypoint (createRoot)
│   │   └── index.css                      ← Global styles + Tailwind directives
│   ├── index.html                         ← Vite HTML template
│   ├── package.json                       ← npm dependencies + scripts
│   ├── tsconfig.json                      ← TypeScript config (strict mode)
│   ├── tsconfig.node.json                 ← TypeScript config for Vite/Node
│   ├── vite.config.ts                     ← Vite config (@ alias for src/)
│   ├── tailwind.config.ts                 ← Tailwind CSS config
│   ├── vitest.config.ts                   ← Vitest test config
│   ├── .env.example                       ← VITE_API_URL placeholder
│   └── components.json                    ← shadcn/ui configuration
│
├── backend/                               ← FastAPI API server (deployed to Render)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        ← FastAPI factory + CORS + router registration + startup
│   │   ├── config.py                      ← pydantic-settings: env var validation
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── health.py              ← GET /health (keepalive endpoint)
│   │   │       ├── users.py               ← POST/GET/PUT /users
│   │   │       ├── onboarding.py          ← POST /onboarding/baseline
│   │   │       ├── activities.py          ← POST/GET/DELETE /activities + POST /activities/parse-nl
│   │   │       ├── carbon.py              ← GET /carbon/summary, /carbon/trends, /carbon/progress
│   │   │       ├── agents.py              ← POST /agents/analyze (SSE), GET /agents/insights
│   │   │       ├── missions.py            ← GET/POST /missions + /accept + /complete
│   │   │       └── chat.py                ← POST /chat/stream (SSE)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── gemini_service.py          ← Centralized Gemini API: function_call(), stream_generate()
│   │   │   ├── carbon_engine.py           ← Deterministic emission calculations (AI-free)
│   │   │   ├── agent_orchestrator.py      ← Sequential pipeline: Analyst → Planner → Coach
│   │   │   └── insights_cache.py          ← SQLite-based 24hr cache with invalidation
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── baseline_agent.py          ← estimate(profile) → BaselineResult
│   │   │   ├── analyst_agent.py           ← analyze(context) → AnalysisResult
│   │   │   ├── planner_agent.py           ← plan(context, analysis) → PlanResult
│   │   │   └── coach_agent.py             ← coach_stream(context, analysis, plan) → AsyncGenerator
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py                 ← All Pydantic request/response/inter-agent models
│   │   │   └── db_models.py               ← SQLite table representations
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py                ← Async connection (aiosqlite), init_db(), get_db()
│   │   │   └── migrations/
│   │   │       └── 001_initial.sql        ← Full schema: 5 tables + 4 indexes (idempotent)
│   │   └── middleware/
│   │       ├── __init__.py
│   │       └── rate_limiter.py            ← In-memory sliding window rate limiter
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                    ← Test DB setup, Gemini mock fixtures, test user fixture
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   ├── test_carbon_engine.py      ← All emission factor calculations + edge cases
│   │   │   ├── test_schemas.py            ← Pydantic model validation (valid + invalid inputs)
│   │   │   └── test_insights_cache.py     ← Cache validity logic + invalidation
│   │   └── integration/
│   │       ├── __init__.py
│   │       ├── test_activities_api.py     ← POST/GET/DELETE activities + NL parse
│   │       ├── test_carbon_api.py         ← GET carbon summary + trends
│   │       └── test_onboarding_api.py     ← POST users + POST baseline
│   ├── .env.example                       ← All backend env vars with placeholders
│   ├── requirements.txt                   ← Python dependencies (pinned versions)
│   ├── Dockerfile                         ← Optional: local Docker build
│   └── pyproject.toml                     ← Python project metadata
│
├── docs/                                  ← All specification documents
│   └── specs/
│       ├── 01-product-requirements.md
│       ├── 02-user-stories-and-acceptance-criteria.md
│       ├── 03-information-architecture.md
│       ├── 04-system-architecture.md
│       ├── 05-database-schema.md
│       ├── 06-api-contracts.md
│       ├── 07-monorepo-structure.md
│       ├── 08-scoring-engine-spec.md
│       ├── 09-engineering-score-definition.md
│       ├── 10-development-phases.md
│       ├── 11-environment-and-devops.md
│       └── 12-testing-strategy.md
│
├── docker-compose.yml                     ← Optional: full-stack local development
├── .gitignore                             ← Comprehensive ignore rules
└── README.md                              ← Competition submission README
```

---

## 3. Module Dependency Graph

### Backend

```
                          ┌────────────────┐
                          │   main.py      │
                          │  (app factory) │
                          └────────┬───────┘
                                   │ registers
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                   ▼
          ┌───────────┐   ┌──────────────┐    ┌──────────────┐
          │ api/v1/*  │   │ config.py    │    │ db/database  │
          │ (routes)  │   │ (settings)   │    │ (init_db)    │
          └─────┬─────┘   └──────────────┘    └──────────────┘
                │ calls                              ▲
                ▼                                    │ reads/writes
          ┌───────────────────┐                      │
          │   services/       │──────────────────────┘
          │   ├ gemini_service│──┐
          │   ├ carbon_engine │  │
          │   ├ orchestrator  │  │
          │   └ insights_cache│  │
          └────────┬──────────┘  │
                   │ calls       │
                   ▼             │
          ┌───────────────┐     │
          │  agents/       │────┘ calls gemini_service
          │  ├ baseline    │
          │  ├ analyst     │
          │  ├ planner     │
          │  └ coach       │
          └────────┬───────┘
                   │ uses
                   ▼
          ┌───────────────┐
          │  models/       │
          │  ├ schemas.py  │  ← used by ALL layers
          │  └ db_models   │
          └───────────────┘
```

### Frontend

```
          ┌───────────┐
          │  App.tsx   │
          │ (root)     │
          └─────┬──────┘
                │
    ┌───────────┼───────────────┐
    ▼           ▼               ▼
 ┌──────┐  ┌────────┐  ┌────────────┐
 │pages/│  │Layout  │  │hooks/      │
 │      │  │(nav)   │  │ useCarbon  │
 │      │  └────┬───┘  │ useStream  │
 │      │       │      │ useMissions│
 └──┬───┘       │      └─────┬──────┘
    │           │            │
    ▼           ▼            ▼
 ┌──────────────────────────────┐
 │     components/               │
 │  Dashboard, ChatInterface,   │
 │  ActivityLogger, MissionCenter│
 │  FootprintPieChart, etc.     │
 └──────────┬───────────────────┘
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
 ┌──────┐ ┌─────┐ ┌──────────┐
 │lib/  │ │ui/  │ │types/    │
 │api.ts│ │shad │ │api.ts    │
 │utils │ │cn   │ │(TS types)│
 └──────┘ └─────┘ └──────────┘
```

---

## 4. File Naming Conventions

| Area | Convention | Examples |
|------|-----------|----------|
| **Frontend components** | PascalCase `.tsx` | `Dashboard.tsx`, `FootprintPieChart.tsx`, `MissionCard.tsx` |
| **Frontend hooks** | camelCase `use*.ts` | `useCarbon.ts`, `useStream.ts`, `useMissions.ts` |
| **Frontend utilities** | kebab-case `.ts` | `user-session.ts`, `keepalive.ts`, `api.ts` |
| **Frontend pages** | PascalCase `.tsx` | `Landing.tsx`, `DashboardPage.tsx`, `ChatPage.tsx` |
| **Frontend types** | camelCase `.ts` | `api.ts` |
| **Backend all files** | snake_case `.py` | `carbon_engine.py`, `gemini_service.py`, `rate_limiter.py` |
| **Backend tests** | `test_*.py` | `test_carbon_engine.py`, `test_activities_api.py` |
| **Migration files** | `NNN_description.sql` | `001_initial.sql` |
| **Docs** | `NN-kebab-case.md` | `01-product-requirements.md` |

---

## 5. Import Path Conventions

### Frontend (`@/` alias for `src/`)

```typescript
// vite.config.ts
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}

// Usage:
import { Dashboard } from '@/components/Dashboard';
import { useCarbon } from '@/hooks/useCarbon';
import { api } from '@/lib/api';
import type { CarbonSummary } from '@/types/api';
```

### Backend (`app.*` absolute imports)

```python
# All imports are absolute from `app` package:
from app.config import settings
from app.services.carbon_engine import calculate_activity_co2
from app.models.schemas import ActivityCreate, ActivityResponse
from app.db.database import get_db
from app.agents.analyst_agent import AnalystAgent
```

---

## 6. `.gitignore` Specification

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.venv/
venv/
*.egg-info/
dist/
build/
*.egg

# Node
node_modules/
dist/
.cache/

# Environment
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
coverage/
htmlcov/
.pytest_cache/
.coverage

# Build
*.tsbuildinfo
```

---

## 7. Environment File Specification

### Backend (`.env`)

```env
# Google Gemini (required — server refuses to start without)
GEMINI_API_KEY=your_gemini_api_key_from_google_ai_studio

# Database (default: local file)
DATABASE_URL=./carbonsense.db

# CORS (comma-separated allowed origins)
ALLOWED_ORIGINS=http://localhost:5173,https://carbonsense.vercel.app

# Rate Limits
RATE_LIMIT_CHAT_RPM=10
RATE_LIMIT_ANALYZE_RPH=3
RATE_LIMIT_NL_RPM=20

# Environment
APP_ENV=development
```

### Frontend (`.env`)

```env
# Backend API base URL
VITE_API_URL=http://localhost:8000
```

### Production Overrides (set in dashboards, never committed)

| Variable | Platform | Value |
|---|---|---|
| `VITE_API_URL` | Vercel | `https://carbonsense-api.onrender.com` |
| `GEMINI_API_KEY` | Render | Google AI Studio API key |
| `DATABASE_URL` | Render | `./carbonsense.db` |
| `ALLOWED_ORIGINS` | Render | `https://carbonsense.vercel.app` |
| `APP_ENV` | Render | `production` |

---

## 8. Package Management

### Frontend: npm

```json
// package.json scripts
{
  "dev": "vite",
  "build": "tsc && vite build",
  "preview": "vite preview",
  "test": "vitest",
  "test:run": "vitest run",
  "lint": "eslint . --ext .ts,.tsx"
}
```

### Backend: pip + requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.1
pydantic-settings==2.3.0
aiosqlite==0.20.0
google-generativeai==0.7.0
httpx==0.27.0
pytest==8.2.2
pytest-asyncio==0.23.7
pytest-cov==5.0.0
```

---

## 9. Size Budget per Folder

| Folder | Estimated Size | Notes |
|---|---|---|
| `frontend/src/` | ~200 KB | TypeScript source, no large assets |
| `frontend/public/` | ~10 KB | Just favicon.svg |
| `backend/app/` | ~100 KB | Python source files |
| `backend/tests/` | ~30 KB | Test files |
| `docs/specs/` | ~200 KB | 12 markdown specification files |
| `.github/` | ~5 KB | CI workflow YAML |
| Root files | ~10 KB | README, docker-compose, .gitignore |
| **Total** | **~555 KB** | Well under 10 MB limit |

**Excluded from repo (`.gitignore`):**
- `node_modules/` (~150 MB)
- `.venv/` (~50 MB)
- `*.db` (SQLite files)
- `dist/` (build output)
- `__pycache__/`
- `.env` (secrets)

---

*Document ends.*
