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

### Phase 16: Production Database & Deployment
- **Supabase Auth**: Integrated Supabase Auth (`AuthContext.tsx`, `AuthPage.tsx`) to manage users securely.
- **Supabase PostgreSQL**: Migrated the database connection string from SQLite to Supabase's IPv4 transaction pooler (`psycopg` async integration).
- **Backend Deployment**: Successfully deployed the FastAPI backend to Render.
- **Frontend Deployment**: Deployed the Vite React frontend to Vercel connected to the Render API and Supabase Auth.

---

## 🐞 Technical Issues & Error Resolutions

| Component | Issue Encountered | Root Cause | Resolution |
| :--- | :--- | :--- | :--- |
| **Database** | SQLite `OperationalError: database is locked` | Concurrent SSE stream writes and user activity logs locked transaction writes. | Enabled Write-Ahead Logging (`WAL` mode) and passed shared connection `db` contexts before committing. |
| **Frontend Tests** | `Cannot find module '../../lib/user-session'` | `require()` calls inside ES module test environments failed to resolve mock instances. | Migrated to a mutable module-level state mock inside `vi.mock('../../lib/user-session')`. |
| **Frontend Tests** | `Unable to find element with text 'Car petrol'` | Case-sensitive text query matched a capitalized element in the DOM differently. | Updated the matcher queries to use case-insensitive regular expressions `/car petrol/i`. |
| **Frontend Build** | `TS18048: 'summary' is possibly 'undefined'` | Operator precedence in `primaryHotspot` evaluation evaluated null properties incorrectly. | Wrapped the fallback expression inside parentheses to enforce correct evaluation hierarchy. |
| **Tailwind CSS** | CSS compilation failed on `border-border` | Tailwind CSS v4 did not load the legacy `tailwind.config.ts` configuration by default. | Installed `@tailwindcss/postcss`, updated `postcss.config.js` and added `@config "../tailwind.config.ts";` in `index.css`. |
| **Deployment** | `Network is unreachable` to `db.*.supabase.co` | Render environments do not support outbound IPv6 which is the default resolution for direct Supabase URLs. | Switched to the Supabase IPv4 Transaction Connection Pooler (`aws-1-...pooler.supabase.com:6543`). |
| **Auth** | `Invalid path specified in request URL` on login | The `VITE_SUPABASE_URL` in Vercel included `/rest/v1` appended to the host. | Reconfigured the environment variable to only include the base host. |
| **Backend** | `unable to open database file` during AI pipeline | The `InsightsCache` service was hardcoded to use `aiosqlite.connect` instead of the multi-dialect db wrapper. | Refactored `insights_cache.py` to use `get_db_context()` to support PostgreSQL. |

---

## 🔮 What to Do Next

1. **Monitor Production Usage**: Keep an eye on Gemini API limits, Render server logs, and Supabase database metrics.
2. **Setup Custom Domains**: Connect custom domains to the Vercel frontend and Render backend endpoints.
3. **Advanced Leaderboards**: Further expand the gamification engine by adding team/company-based leaderboards.
4. **Enhanced Data Visualizations**: Integrate libraries like D3.js to build more interactive user footprint heatmaps over time.
