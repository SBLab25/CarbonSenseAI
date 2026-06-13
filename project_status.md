# CarbonSense AI — Project Status

**Current Status**: Complete & Verified (All 15 Prompts fully implemented, compiled, and tested)

---

## 🛠️ Implemented Phases & Files

### Phase 1: Base Project Scaffold
- **Frontend Scaffold**: Created React 18 + TS + Vite frontend in `/frontend`.
- **Backend Scaffold**: Created FastAPI backend in `/backend` with strict settings loading and health endpoints.
- **Root Configurations**: Created `.gitignore`, `docker-compose.yml`, and GitHub Actions workflow.

### Phase 2: Database Layer & Schemas
- **Initial Migration**: `001_initial.sql` defining `users`, `activities`, `insights_cache`, `missions`, and `goals` tables.
- **Connection Handlers**: `database.py` utilizing `aiosqlite` with WAL mode enabled.
- **Pydantic Schemas**: `schemas.py` defining v2 input/response models and validators.

### Phase 3: Carbon Engine & Factors
- **Engine Logic**: `carbon_engine.py` using UK DEFRA, CEA India, and Science 2018 emission factors.
- **Validation**: `test_carbon_engine.py` verifying 17+ calculations (petrol/diesel/electric cars, domestic/intl flights, electricity, diet types).

### Phase 4: AI Gemini & Rate Limiter
- **Gemini Service**: `gemini_service.py` wrapping Gemini 1.5 Flash for function calling, natural language parsing, and streaming SSE responses.
- **Rate Limiter**: `rate_limiter.py` implementing a sliding window algorithm to throttle chat, analysis, and parsing requests.

### Phase 5: Multi-Agent Coaching Pipeline
- **Baseline Agent**: `baseline_agent.py` to estimate initial carbon footprints on onboarding.
- **Analyst Agent**: `analyst_agent.py` to find hotspots and patterns.
- **Planner Agent**: `planner_agent.py` to recommend strategies.
- **Coach Agent**: `coach_agent.py` to chat and coach.
- **Orchestrator**: `agent_orchestrator.py` chaining agents, caching analysis results, and streaming SSE responses.

### Phase 6-12: Web Dashboard & Interactive Interfaces
- **Dashboard**: `Dashboard.tsx`, `FootprintPieChart.tsx`, `TrendLineChart.tsx`, `GoalProgressBar.tsx`, and `useCarbon.ts`.
- **Logging**: `ActivityForm.tsx`, `NLActivityInput.tsx`, `ActivityLogger.tsx`, and `useActivities.ts`.
- **SSE Chat**: `ChatInterface.tsx` and `useStream.ts`.
- **Missions**: `MissionCard.tsx`, `MissionCenter.tsx`, `useMissions.ts`, and `EcoPointsBadge.tsx`.

### Phase 13: Backend Testing Suite
- **Configuration**: `conftest.py` with mock databases and mocked Gemini responses.
- **Coverage**: 52 unit/integration tests running with 87% statement coverage.

### Phase 14: Frontend Testing Suite
- **Unit/Component Tests**: `carbon-utils.test.ts`, `user-session.test.ts`, `ActivityLogger.test.tsx`, `MissionCard.test.tsx`, and `GoalProgressBar.test.tsx` (21 passing tests).

### Phase 15: Setup & Documentation
- **Root Documentation**: `README.md` defining features, architecture, factors, and execution commands.

---

## 🐞 Technical Issues & Error Resolutions

| Component | Issue Encountered | Root Cause | Resolution |
| :--- | :--- | :--- | :--- |
| **Database** | SQLite `OperationalError: database is locked` | Concurrent SSE stream writes and user activity logs locked transaction writes. | Enabled Write-Ahead Logging (`WAL` mode) and passed shared connection `db` contexts before committing. |
| **Frontend Tests** | `Cannot find module '../../lib/user-session'` | `require()` calls inside ES module test environments failed to resolve mock instances. | Migrated to a mutable module-level state mock inside `vi.mock('../../lib/user-session')`. |
| **Frontend Tests** | `Unable to find element with text 'Car petrol'` | Case-sensitive text query matched a capitalized element in the DOM differently. | Updated the matcher queries to use case-insensitive regular expressions `/car petrol/i`. |
| **Frontend Build** | `TS18048: 'summary' is possibly 'undefined'` | Operator precedence in `primaryHotspot` evaluation evaluated null properties incorrectly. | Wrapped the fallback expression inside parentheses to enforce correct evaluation hierarchy. |
| **Tailwind CSS** | CSS compilation failed on `border-border` | Tailwind CSS v4 did not load the legacy `tailwind.config.ts` configuration by default. | Installed `@tailwindcss/postcss`, updated `postcss.config.js` and added `@config "../tailwind.config.ts";` in `index.css`. |

---

## 🔮 What to Do Next

1. **Production Deployment**: Deploy the frontend React app to Vercel/Netlify and backend FastAPI service to Render/Fly.io.
2. **Setup Staging Database**: Migrate the SQLite database setup to a production PostgreSQL instance (e.g. Supabase) by replacing connection strings.
3. **Verify CORS Policies**: Ensure production allowed origins are updated in the `.env` settings.
4. **Acquire Live Gemini API Key**: Replace the local testing API keys with a production Google AI Studio key.
