# CarbonSense AI — Engineering Score Definition

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. Purpose

This document defines the engineering quality standards and scoring rubric that CarbonSense AI must meet to maximize its PromptWars competition evaluation score. Each criterion maps to specific implementation evidence the evaluator can verify.

---

## 2. Competition Scoring Criteria

The PromptWars Challenge 3 evaluation covers five engineering dimensions. Based on PRD analysis, the implied scoring breakdown is:

| # | Criterion | Weight | What Evaluator Checks |
|---|---|---|---|
| 1 | **Code Quality & Architecture** | ~25% | Structure, readability, modularity, naming, TypeScript strictness, separation of concerns |
| 2 | **Security Best Practices** | ~20% | Secret management, CORS, input validation, rate limiting, no PII exposure |
| 3 | **Efficiency & Performance** | ~20% | Response times, caching, API call optimization, resource usage |
| 4 | **Testing Coverage** | ~20% | Automated tests, coverage reports, test strategy document |
| 5 | **Accessibility (a11y)** | ~15% | WCAG 2.1 AA, ARIA labels, keyboard navigation, color contrast |

### Score Multiplier

```
Final Score = Base Score × Time Multiplier
```

Earlier submissions receive a higher time multiplier (decays over the competition period). Maximum 3 submission attempts; each overwrites the previous score.

---

## 3. Criterion 1 — Code Quality & Architecture

### 3.1 Evidence Map

| Quality Signal | Implementation Evidence | File/Location |
|---|---|---|
| Layered architecture | API → Service → Agent → Domain → Infrastructure (no layer skipping) | `backend/app/` directory structure |
| Single Responsibility | Each file/class has one job: `carbon_engine.py` calculates, `gemini_service.py` calls API | `backend/app/services/*.py`, `backend/app/agents/*.py` |
| TypeScript strict mode | `tsconfig.json` with `"strict": true`, `"noImplicitAny": true` | `frontend/tsconfig.json` |
| Pydantic v2 schemas | Every request/response has a typed schema — no raw dicts | `backend/app/models/schemas.py` |
| Consistent naming | snake_case Python, PascalCase React components, camelCase hooks | Project-wide |
| Import organization | Absolute imports (`from app.services.carbon_engine import ...`) | All Python files |
| Path aliases | `@/` alias for `src/` in frontend imports | `frontend/vite.config.ts` |
| No circular dependencies | Strict layer rules prevent import cycles | Module dependency graph |
| Docstrings & comments | All public functions documented; emission factors have source citations | `carbon_engine.py`, all agents |

### 3.2 Architecture Compliance Rules

```
✅ ALLOWED:  API Layer → Service Layer → Agent Layer
✅ ALLOWED:  Service Layer → Domain Layer (Pydantic schemas)
✅ ALLOWED:  Agent Layer → GeminiService
❌ BLOCKED:  API Layer → Agent Layer (must go through Service)
❌ BLOCKED:  Agent Layer → Database (must go through Service)
❌ BLOCKED:  Any Layer → API Layer (no upward dependencies)
```

### 3.3 Scoring Checklist

- [ ] `tsconfig.json` has `strict: true`
- [ ] All Python functions have docstrings
- [ ] All emission factors have inline source citation comments
- [ ] No `any` types in TypeScript (checked by ESLint)
- [ ] No raw `dict` returns in FastAPI routes (all Pydantic-typed)
- [ ] Backend `__init__.py` files present in all packages
- [ ] Frontend components have descriptive file names (PascalCase)
- [ ] Custom hooks follow `use*` naming convention
- [ ] No business logic in route handlers (all delegated to services)
- [ ] Error types are custom classes (not generic `Exception`)

---

## 4. Criterion 2 — Security Best Practices

### 4.1 Evidence Map

| Security Practice | Implementation | File/Location |
|---|---|---|
| Secret management | `GEMINI_API_KEY` in `.env`, never committed; `.gitignore` includes `.env*` | `.env.example`, `.gitignore` |
| CORS configuration | `ALLOWED_ORIGINS` from env var, never `*` in production | `backend/app/main.py` (CORS middleware) |
| Input validation | Every endpoint validates via Pydantic v2 models | `backend/app/models/schemas.py` |
| Rate limiting | Sliding window rate limiter on AI endpoints | `backend/app/middleware/rate_limiter.py` |
| Error sanitization | Raw exceptions never sent to frontend; all errors shaped to `{"detail": "..."}` | `backend/app/main.py` (exception handler) |
| No PII in localStorage | Only UUID stored client-side | `frontend/src/lib/user-session.ts` |
| No hardcoded secrets | All secrets loaded from environment variables | `backend/app/config.py` (pydantic-settings) |
| Dependency pinning | All Python packages pinned to exact versions | `backend/requirements.txt` |

### 4.2 CORS Configuration

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # from ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production:** `ALLOWED_ORIGINS=https://carbonsense.vercel.app`  
**Development:** `ALLOWED_ORIGINS=http://localhost:5173`  
**Never:** `ALLOWED_ORIGINS=*`

### 4.3 Rate Limiting Strategy

| Endpoint | Limit | Window | Purpose |
|---|---|---|---|
| `POST /agents/analyze` | 3 | per hour | Prevent Gemini API abuse |
| `POST /chat/stream` | 10 | per minute | Prevent chat spam |
| `POST /activities/parse-nl` | 20 | per minute | Prevent NL parsing spam |

### 4.4 Scoring Checklist

- [ ] `.env.example` exists with placeholder values
- [ ] `.gitignore` contains `.env`, `.env.local`, `.env.*.local`
- [ ] `config.py` uses `pydantic-settings` (not `os.getenv` directly)
- [ ] CORS `allow_origins` reads from env var (not hardcoded)
- [ ] All API inputs validated via Pydantic schemas
- [ ] Rate limiter applied to AI-calling endpoints
- [ ] Global exception handler prevents raw error exposure
- [ ] No `console.log(apiKey)` or similar in frontend
- [ ] `localStorage` stores only UUID (no tokens, no PII)
- [ ] All Python deps pinned to exact versions (`==`)

---

## 5. Criterion 3 — Efficiency & Performance

### 5.1 Evidence Map

| Optimization | Mechanism | Impact |
|---|---|---|
| Gemini 1.5 Flash | Lowest-latency Gemini model; avg 600ms first token | Agent pipeline ≤ 10s |
| SSE streaming | Coach Agent streams tokens in real-time | Perceived latency near-zero |
| Insight cache (24hr) | Skip Analyst + Planner if cache valid | ~60% of analysis calls skip Gemini |
| React Query cache | `staleTime=5min` for all server state | Dashboard loads instantly on navigation |
| SQLite aggregation | `GROUP BY` queries for category/trend totals | Dashboard queries < 50ms |
| Vercel CDN | Static assets served from edge globally | FCP < 1.5s |
| Keepalive ping | 14-min interval prevents Render free-tier spin-down | No cold start delays |
| Minimal context principle | Each agent receives only the data it needs | Smaller Gemini payloads = faster |
| Async FastAPI | All I/O is `async`/`await` (aiosqlite, httpx) | No thread blocking |

### 5.2 Performance Targets

| Metric | Target | How Verified |
|---|---|---|
| FCP (First Contentful Paint) | ≤ 2.0s | Lighthouse audit |
| API P95 latency (non-AI) | ≤ 500ms | Backend logging |
| AI first token (streaming) | ≤ 2.0s | SSE stream timing |
| Full agent pipeline | ≤ 10.0s | End-to-end pipeline timing |
| Dashboard SQL queries | < 50ms | SQLite query logging |
| Frontend bundle size | < 500 KB gzipped | Vite build report |

### 5.3 Cache Hit Workflow

```
Analyze request → Check insights_cache
  ├── HIT (is_valid=1 AND valid_until > now)
  │     └── Skip Analyst + Planner → Run Coach from cached data → ~3s response
  └── MISS (cache expired or invalidated by new activity)
        └── Run full pipeline: Analyst → Planner → Coach → ~8s response
```

### 5.4 Scoring Checklist

- [ ] `staleTime` configured in React Query (not default 0)
- [ ] Insight cache implemented with 24hr TTL + activity invalidation
- [ ] SSE streaming implemented (not buffered full response)
- [ ] `X-Accel-Buffering: no` header set on SSE endpoints
- [ ] Keepalive ping implemented in `useKeepalive` hook
- [ ] All database calls use `async`/`await` (aiosqlite)
- [ ] Indexes created on frequently-queried columns
- [ ] Minimal context principle enforced in agent inputs
- [ ] Vite build produces < 500 KB gzipped bundle

---

## 6. Criterion 4 — Testing Coverage

### 6.1 Evidence Map

| Test Layer | Framework | Coverage Target | Files |
|---|---|---|---|
| Backend unit tests | pytest | ≥ 90% on carbon_engine | `tests/unit/test_carbon_engine.py` |
| Backend schema tests | pytest | ≥ 80% on schemas | `tests/unit/test_schemas.py` |
| Backend integration tests | pytest + httpx | ≥ 80% on API routes | `tests/integration/test_*_api.py` |
| Agent orchestrator tests | pytest (mocked Gemini) | ≥ 70% on orchestrator | `tests/unit/test_orchestrator.py` |
| Frontend component tests | Vitest + React Testing Library | ≥ 60% on components | `frontend/src/**/*.test.tsx` |
| CI pipeline | GitHub Actions | All tests pass on push to main | `.github/workflows/ci.yml` |

### 6.2 Backend Test Inventory

```
tests/
├── conftest.py                       ← Fresh SQLite per session, Gemini mock fixtures
├── unit/
│   ├── test_carbon_engine.py         ← 15+ test cases:
│   │   ├── test_car_petrol_calculation
│   │   ├── test_bicycle_zero_emission
│   │   ├── test_electricity_india_grid
│   │   ├── test_beef_high_emission
│   │   ├── test_unknown_type_returns_zero
│   │   ├── test_zero_amount
│   │   ├── test_all_transport_factors_positive_or_zero
│   │   ├── test_india_comparison
│   │   ├── test_eco_tier_seedling
│   │   ├── test_eco_tier_sapling
│   │   ├── test_eco_tier_tree
│   │   ├── test_eco_tier_forest
│   │   └── test_eco_tier_boundary
│   ├── test_schemas.py               ← 10+ test cases:
│   │   ├── test_valid_activity_create
│   │   ├── test_invalid_category_rejected
│   │   ├── test_negative_amount_rejected
│   │   ├── test_name_required
│   │   └── test_valid_user_create
│   └── test_insights_cache.py        ← 5+ test cases:
│       ├── test_cache_miss_on_empty
│       ├── test_cache_hit_within_ttl
│       ├── test_cache_miss_after_ttl
│       ├── test_cache_invalidation_on_activity
│       └── test_cache_miss_when_invalid
├── integration/
│   ├── test_activities_api.py        ← 5+ test cases:
│   │   ├── test_log_activity_calculates_co2
│   │   ├── test_get_activity_history
│   │   ├── test_delete_activity
│   │   ├── test_activity_validation_error
│   │   └── test_nl_parse_activity
│   ├── test_carbon_api.py            ← 3+ test cases:
│   │   ├── test_carbon_summary_with_data
│   │   ├── test_carbon_summary_empty
│   │   └── test_carbon_trends
│   └── test_onboarding_api.py        ← 3+ test cases:
│       ├── test_create_user
│       ├── test_create_user_validation
│       └── test_health_endpoint
```

### 6.3 Test Commands

```bash
# Backend: run all tests with coverage
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend: run all tests (single run for CI)
cd frontend
npm run test:run

# Frontend: run tests in watch mode (development)
cd frontend
npm run test
```

### 6.4 CI Pipeline (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v --cov=app --cov-report=term-missing
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          DATABASE_URL: ./test.db
          ALLOWED_ORIGINS: http://localhost:5173

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
        working-directory: frontend
      - run: npm run test:run
        working-directory: frontend
```

### 6.5 Scoring Checklist

- [ ] `pytest` configured with `conftest.py` (test DB isolation)
- [ ] Carbon Engine has ≥ 15 unit tests
- [ ] Schema validation has ≥ 10 unit tests (valid + invalid)
- [ ] Integration tests use `httpx.AsyncClient` with `ASGITransport`
- [ ] Gemini API calls mocked in orchestrator tests (no real API calls in CI)
- [ ] GitHub Actions workflow file exists and runs on push to main
- [ ] Coverage report generated (`--cov-report=term-missing`)
- [ ] Frontend test scripts defined in `package.json` (`test`, `test:run`)
- [ ] At least 3 frontend component tests exist

---

## 7. Criterion 5 — Accessibility (a11y)

### 7.1 Evidence Map

| a11y Standard | Implementation | Where |
|---|---|---|
| WCAG 2.1 AA | shadcn/ui components are WCAG-compliant out of box | All UI components |
| ARIA labels | All charts, buttons, and interactive elements labeled | Recharts `aria-label`, Button `aria-label` |
| Keyboard navigation | Full tab-order navigation across all pages | Layout, forms, chat input |
| Focus management | Focus moves to `<h1>` on route change | React Router `useEffect` |
| Color contrast | 4.5:1 minimum ratio on all text | Tailwind config, shadcn themes |
| Screen reader support | Semantic HTML (`<main>`, `<nav>`, `<section>`, `<h1>`–`<h3>`) | All page components |
| Form accessibility | Labels linked to inputs via `htmlFor` / `id` | Onboarding form, Activity form |
| Error announcements | Validation errors announced to screen readers | `aria-live="polite"` on error containers |

### 7.2 Chart Accessibility

```tsx
// FootprintPieChart.tsx
<PieChart aria-label="Category breakdown of your carbon footprint">
  <Pie
    data={data}
    nameKey="category"
    dataKey="kg"
    aria-label="Pie chart showing emission percentage by category"
  >
    {data.map((entry) => (
      <Cell
        key={entry.category}
        fill={COLORS[entry.category]}
        aria-label={`${entry.category}: ${entry.pct}% of total`}
      />
    ))}
  </Pie>
  <Tooltip />
  <Legend />
</PieChart>
```

### 7.3 Focus Management on Navigation

```tsx
// Layout.tsx or App.tsx
useEffect(() => {
  const h1 = document.querySelector('h1');
  if (h1) {
    h1.setAttribute('tabindex', '-1');
    h1.focus();
  }
}, [location.pathname]);
```

### 7.4 Semantic HTML Structure

```html
<!-- Every page follows this structure -->
<main>
  <h1>Page Title</h1>
  <section aria-label="Section description">
    <!-- Section content -->
  </section>
</main>
```

### 7.5 Scoring Checklist

- [ ] `<h1>` present on every page (exactly one per page)
- [ ] Semantic `<main>`, `<nav>`, `<section>` used (not all `<div>`)
- [ ] All Recharts charts have `aria-label` props
- [ ] All form inputs have associated `<label>` elements
- [ ] Focus moves to page heading on route change
- [ ] Error messages are in `aria-live="polite"` containers
- [ ] Color contrast ≥ 4.5:1 verified on all text
- [ ] Tab key navigates through all interactive elements in logical order
- [ ] Skip-to-content link present (optional but bonus)
- [ ] No `<img>` without `alt` attribute

---

## 8. Submission Strategy

### 8.1 Submission Rules

- Maximum 3 submission attempts
- Each submission overwrites the previous score
- Earlier submissions receive a higher time multiplier
- Score = Base Score × Time Multiplier

### 8.2 Recommended Submission Plan

| Attempt | When | Purpose |
|---|---|---|
| 1 | Day 6 (core features done) | Lock in a base score with functioning core |
| 2 | Day 9 (polish done) | Improve score with full test coverage + a11y |
| 3 | Day 12 (final, pre-deadline) | Final polished submission if score improved |

### 8.3 Pre-Submission Verification

```bash
# 1. Run all tests
cd backend && pytest tests/ -v --cov=app --cov-report=term-missing
cd frontend && npm run test:run

# 2. Build check
cd frontend && npm run build   # Should succeed with no errors

# 3. Check repo size
git bundle create /tmp/repo.bundle --all
ls -lh /tmp/repo.bundle        # Must be < 10 MB

# 4. Lighthouse audit
# Run Chrome DevTools Lighthouse on deployed frontend
# Check: Performance > 90, Accessibility > 90

# 5. Verify .env.example files exist (no real secrets)
cat backend/.env.example
cat frontend/.env.example

# 6. Verify README.md
# Must document: vertical chosen, approach, how solution works, assumptions
```

---

## 9. Score Optimization Matrix

| Investment Area | Time (hrs) | Score Impact | Priority |
|---|---|---|---|
| Carbon Engine tests (90% coverage) | 2 | High — Testing criterion | P0 |
| Pydantic schemas for all endpoints | 3 | High — Code Quality + Security | P0 |
| CORS + Rate limiting middleware | 2 | High — Security criterion | P0 |
| ARIA labels on all charts | 1 | Medium — Accessibility criterion | P0 |
| Insight cache implementation | 3 | High — Efficiency criterion | P0 |
| SSE streaming (Coach Agent) | 3 | High — Efficiency criterion | P0 |
| Integration tests (API routes) | 3 | Medium — Testing criterion | P1 |
| Frontend component tests | 4 | Medium — Testing criterion | P1 |
| Keyboard navigation verification | 2 | Medium — Accessibility criterion | P1 |
| README.md with full documentation | 1 | Medium — Code Quality | P1 |
| GitHub Actions CI pipeline | 1 | Medium — Testing criterion | P1 |
| Lighthouse performance optimization | 2 | Low — Vercel CDN handles most | P2 |

---

*Document ends.*
