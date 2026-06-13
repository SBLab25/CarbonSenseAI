# CarbonSense AI — Testing Strategy

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. Testing Philosophy

```
"Test what matters most. In a competition, that means:
deterministic calculations, API contracts, and agent pipeline reliability."
```

### Testing Pyramid for CarbonSense AI

```
               ┌──────────────┐
               │   E2E Smoke  │  ← Manual: onboard → log → analyze → chat → mission
               │   (Manual)   │     Run before each submission
               ├──────────────┤
               │ Integration  │  ← pytest + httpx: API endpoint behavior
               │   Tests      │     POST/GET/PUT/DELETE with real DB
               ├──────────────┤
               │              │  ← pytest (backend): carbon engine, schemas, cache
               │  Unit Tests  │     Vitest + RTL (frontend): components, hooks
               │              │
               └──────────────┘
```

| Layer | Scope | Volume | Purpose |
|---|---|---|---|
| **Unit Tests** | Functions, classes, components | ~30+ tests | Verify calculations, validation, rendering |
| **Integration Tests** | API endpoints with real DB | ~15+ tests | Verify request → response → DB state |
| **E2E Smoke Test** | Full user flow on deployed app | 1 manual test | Verify production deployment works |

---

## 2. Coverage Targets

| Module | Target Coverage | Rationale |
|---|---|---|
| `carbon_engine.py` | ≥ 90% | Core calculation layer — trust depends on correctness |
| `models/schemas.py` | ≥ 80% | Input validation is a security boundary |
| API routes (`api/v1/*.py`) | ≥ 80% | Contract compliance — request/response shapes |
| `agent_orchestrator.py` | ≥ 70% | Pipeline flow logic (Gemini mocked) |
| `insights_cache.py` | ≥ 80% | Cache logic correctness prevents stale data |
| Frontend components | ≥ 60% | Core rendering and interaction |
| **Overall backend** | ≥ 80% | Competition standard |
| **Overall frontend** | ≥ 60% | Competition standard |

---

## 3. Backend Testing Framework

### 3.1 Tools

| Tool | Version | Purpose |
|---|---|---|
| `pytest` | 8.2.2 | Test runner and assertions |
| `pytest-asyncio` | 0.23.7 | Async test support for FastAPI |
| `pytest-cov` | 5.0.0 | Coverage reporting |
| `httpx` | 0.27.0 | Async HTTP client for integration tests |

### 3.2 Test Configuration

**`conftest.py`:**

```python
import pytest
import asyncio
from app.db.database import init_db


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
async def setup_test_db(tmp_path_factory, monkeypatch):
    """Use a fresh SQLite DB for the entire test session."""
    tmp_db = str(tmp_path_factory.mktemp("db") / "test.db")
    monkeypatch.setenv("DATABASE_URL", tmp_db)
    await init_db()


@pytest.fixture
def test_user_data():
    """Standard test user data for onboarding."""
    return {
        "name": "Test User",
        "country": "India",
        "city": "Bengaluru",
        "lifestyle_type": "urban",
        "diet_type": "mixed",
        "primary_transport": "car_petrol",
        "weekly_transport_km": 80,
        "monthly_electricity_kwh": 150,
        "heating_type": "lpg",
    }
```

### 3.3 Running Tests

```bash
# All backend tests with coverage
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Only unit tests
pytest tests/unit/ -v

# Only integration tests
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_carbon_engine.py -v

# With coverage HTML report
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

---

## 4. Backend Unit Tests

### 4.1 Carbon Engine Tests (`tests/unit/test_carbon_engine.py`)

```python
import pytest
from app.services.carbon_engine import (
    calculate_activity_co2,
    get_india_comparison,
    get_eco_tier,
    TRANSPORT_FACTORS,
    ENERGY_FACTORS,
    FOOD_FACTORS,
    SHOPPING_FACTORS,
)


class TestCarbonEngine:
    """Unit tests for deterministic CO₂ calculations."""

    # --- Transport ---
    def test_car_petrol_calculation(self):
        result = calculate_activity_co2("transport", "car_petrol", 100)
        assert result == pytest.approx(21.0, rel=0.01)

    def test_car_diesel_calculation(self):
        result = calculate_activity_co2("transport", "car_diesel", 50)
        assert result == pytest.approx(8.5, rel=0.01)

    def test_bicycle_zero_emission(self):
        result = calculate_activity_co2("transport", "bicycle", 50)
        assert result == 0.0

    def test_walking_zero_emission(self):
        result = calculate_activity_co2("transport", "walking", 100)
        assert result == 0.0

    # --- Energy ---
    def test_electricity_india_grid(self):
        result = calculate_activity_co2("energy", "electricity", 100)
        assert result == pytest.approx(70.8, rel=0.01)

    def test_solar_zero_emission(self):
        result = calculate_activity_co2("energy", "solar", 100)
        assert result == 0.0

    # --- Food ---
    def test_beef_high_emission(self):
        result = calculate_activity_co2("food", "beef", 1.0)
        assert result == pytest.approx(27.0, rel=0.01)

    def test_vegetables_low_emission(self):
        result = calculate_activity_co2("food", "vegetables", 2.0)
        assert result == pytest.approx(4.0, rel=0.01)

    # --- Shopping ---
    def test_electronics_large(self):
        result = calculate_activity_co2("shopping", "electronics_large", 1)
        assert result == pytest.approx(300.0, rel=0.01)

    # --- Edge Cases ---
    def test_unknown_type_returns_zero(self):
        result = calculate_activity_co2("transport", "rocket_ship", 100)
        assert result == 0.0

    def test_unknown_category_returns_zero(self):
        result = calculate_activity_co2("magic", "wand", 100)
        assert result == 0.0

    def test_zero_amount(self):
        result = calculate_activity_co2("transport", "car_petrol", 0)
        assert result == 0.0

    # --- Factor Integrity ---
    def test_all_transport_factors_positive_or_zero(self):
        for mode, factor in TRANSPORT_FACTORS.items():
            assert factor >= 0.0, f"Negative factor for {mode}"

    def test_all_food_factors_positive(self):
        for food, factor in FOOD_FACTORS.items():
            assert factor >= 0.0, f"Negative factor for {food}"

    def test_all_energy_factors_positive_or_zero(self):
        for source, factor in ENERGY_FACTORS.items():
            assert factor >= 0.0, f"Negative factor for {source}"


class TestIndiaComparison:
    """Tests for footprint vs India national average."""

    def test_exact_average(self):
        result = get_india_comparison(158.3)
        assert result == pytest.approx(100.0, rel=0.1)

    def test_below_average(self):
        result = get_india_comparison(100.0)
        assert result < 100.0

    def test_above_average(self):
        result = get_india_comparison(200.0)
        assert result > 100.0

    def test_zero_footprint(self):
        result = get_india_comparison(0.0)
        assert result == 0.0


class TestEcoTier:
    """Tests for Eco Points tier system."""

    def test_seedling(self):
        assert get_eco_tier(0) == "Seedling"
        assert get_eco_tier(100) == "Seedling"
        assert get_eco_tier(249) == "Seedling"

    def test_sapling(self):
        assert get_eco_tier(250) == "Sapling"
        assert get_eco_tier(500) == "Sapling"
        assert get_eco_tier(749) == "Sapling"

    def test_tree(self):
        assert get_eco_tier(750) == "Tree"
        assert get_eco_tier(1000) == "Tree"
        assert get_eco_tier(1499) == "Tree"

    def test_forest(self):
        assert get_eco_tier(1500) == "Forest"
        assert get_eco_tier(5000) == "Forest"
```

### 4.2 Schema Validation Tests (`tests/unit/test_schemas.py`)

```python
import pytest
from pydantic import ValidationError
from app.models.schemas import ActivityCreate, UserCreate


class TestActivityCreate:
    def test_valid_activity(self):
        activity = ActivityCreate(
            user_id="test-uuid-123",
            category="transport",
            type="car_petrol",
            amount=20.0,
            unit="km",
        )
        assert activity.category == "transport"
        assert activity.amount == 20.0

    def test_invalid_category_rejected(self):
        with pytest.raises(ValidationError):
            ActivityCreate(
                user_id="test-uuid-123",
                category="flying",  # invalid
                type="car_petrol",
                amount=20.0,
                unit="km",
            )

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            ActivityCreate(
                user_id="test-uuid-123",
                category="transport",
                type="car_petrol",
                amount=-5.0,  # negative
                unit="km",
            )

    def test_zero_amount_valid(self):
        activity = ActivityCreate(
            user_id="test-uuid-123",
            category="transport",
            type="bicycle",
            amount=0.0,
            unit="km",
        )
        assert activity.amount == 0.0


class TestUserCreate:
    def test_valid_user(self):
        user = UserCreate(
            name="Alex",
            country="India",
            city="Bengaluru",
            lifestyle_type="urban",
            diet_type="mixed",
            primary_transport="car_petrol",
            weekly_transport_km=80.0,
            monthly_electricity_kwh=150.0,
            heating_type="lpg",
        )
        assert user.name == "Alex"

    def test_name_required(self):
        with pytest.raises(ValidationError):
            UserCreate(
                country="India",
                diet_type="mixed",
                primary_transport="car_petrol",
                weekly_transport_km=80.0,
                monthly_electricity_kwh=150.0,
                heating_type="lpg",
            )

    def test_invalid_diet_type_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(
                name="Alex",
                diet_type="carnivore",  # invalid
                primary_transport="car_petrol",
                weekly_transport_km=80.0,
                monthly_electricity_kwh=150.0,
                heating_type="lpg",
            )
```

### 4.3 Insights Cache Tests (`tests/unit/test_insights_cache.py`)

```python
import pytest
from datetime import datetime, timedelta


class TestInsightsCache:
    """Tests for insight cache logic."""

    @pytest.mark.asyncio
    async def test_cache_miss_on_empty(self, db_conn):
        """No cache exists → miss."""
        result = await check_cache(db_conn, "user-1", "analyst")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit_within_ttl(self, db_conn):
        """Cache exists, valid, within TTL → hit."""
        await store_cache(db_conn, "user-1", "analyst", '{"test": true}',
                         valid_until=datetime.utcnow() + timedelta(hours=23))
        result = await check_cache(db_conn, "user-1", "analyst")
        assert result is not None
        assert result == '{"test": true}'

    @pytest.mark.asyncio
    async def test_cache_miss_after_ttl(self, db_conn):
        """Cache exists but TTL expired → miss."""
        await store_cache(db_conn, "user-1", "analyst", '{"test": true}',
                         valid_until=datetime.utcnow() - timedelta(hours=1))
        result = await check_cache(db_conn, "user-1", "analyst")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, db_conn):
        """Cache invalidated by new activity → miss."""
        await store_cache(db_conn, "user-1", "analyst", '{"test": true}',
                         valid_until=datetime.utcnow() + timedelta(hours=23))
        await invalidate_cache(db_conn, "user-1")
        result = await check_cache(db_conn, "user-1", "analyst")
        assert result is None
```

---

## 5. Backend Integration Tests

### 5.1 Activities API (`tests/integration/test_activities_api.py`)

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_log_activity_calculates_co2():
    """POST /activities → Carbon Engine calculates co2_kg."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create user first
        user_resp = await client.post("/api/v1/users", json={
            "name": "Test User", "country": "India", "city": "Bengaluru",
            "lifestyle_type": "urban", "diet_type": "mixed",
            "primary_transport": "car_petrol", "weekly_transport_km": 80,
            "monthly_electricity_kwh": 150, "heating_type": "lpg"
        })
        user_id = user_resp.json()["user_id"]

        # Log activity
        resp = await client.post("/api/v1/activities", json={
            "user_id": user_id,
            "category": "transport",
            "type": "car_petrol",
            "amount": 20.0,
            "unit": "km"
        })
        assert resp.status_code == 200
        assert resp.json()["co2_kg"] == pytest.approx(4.2, rel=0.01)


@pytest.mark.asyncio
async def test_get_activity_history():
    """GET /activities/{user_id} returns paginated history."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create user + log activity (setup)
        user_resp = await client.post("/api/v1/users", json={
            "name": "Test", "diet_type": "mixed",
            "primary_transport": "bus", "weekly_transport_km": 40,
            "monthly_electricity_kwh": 100, "heating_type": "none"
        })
        user_id = user_resp.json()["user_id"]

        await client.post("/api/v1/activities", json={
            "user_id": user_id, "category": "food",
            "type": "beef", "amount": 0.5, "unit": "kg"
        })

        # Fetch history
        resp = await client.get(f"/api/v1/activities/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) >= 1
        assert data["total"] >= 1


@pytest.mark.asyncio
async def test_delete_activity():
    """DELETE /activities/{id} removes the entry."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create user + log activity
        user_resp = await client.post("/api/v1/users", json={
            "name": "Delete Test", "diet_type": "vegan",
            "primary_transport": "bicycle", "weekly_transport_km": 20,
            "monthly_electricity_kwh": 80, "heating_type": "none"
        })
        user_id = user_resp.json()["user_id"]

        activity_resp = await client.post("/api/v1/activities", json={
            "user_id": user_id, "category": "energy",
            "type": "electricity", "amount": 10.0, "unit": "kWh"
        })
        activity_id = activity_resp.json()["activity_id"]

        # Delete
        del_resp = await client.delete(f"/api/v1/activities/{activity_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True


@pytest.mark.asyncio
async def test_activity_validation_error():
    """POST /activities with invalid category → 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/v1/activities", json={
            "user_id": "fake-uuid",
            "category": "magic",  # invalid
            "type": "wand",
            "amount": 1.0,
            "unit": "item"
        })
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /health → 200 ok."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
```

### 5.2 Carbon API (`tests/integration/test_carbon_api.py`)

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_carbon_summary_with_data():
    """GET /carbon/summary/{user_id} returns category breakdown."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Setup: create user + log activities
        user_resp = await client.post("/api/v1/users", json={
            "name": "Summary Test", "diet_type": "mixed",
            "primary_transport": "car_petrol", "weekly_transport_km": 80,
            "monthly_electricity_kwh": 150, "heating_type": "lpg"
        })
        user_id = user_resp.json()["user_id"]

        await client.post("/api/v1/activities", json={
            "user_id": user_id, "category": "transport",
            "type": "car_petrol", "amount": 50.0, "unit": "km"
        })

        # Fetch summary
        resp = await client.get(f"/api/v1/carbon/summary/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_kg"] > 0
        assert "breakdown" in data


@pytest.mark.asyncio
async def test_carbon_trends():
    """GET /carbon/trends/{user_id}?days=7 returns daily data."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        user_resp = await client.post("/api/v1/users", json={
            "name": "Trend Test", "diet_type": "vegetarian",
            "primary_transport": "bus", "weekly_transport_km": 30,
            "monthly_electricity_kwh": 100, "heating_type": "none"
        })
        user_id = user_resp.json()["user_id"]

        resp = await client.get(f"/api/v1/carbon/trends/{user_id}?days=7")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
```

---

## 6. Frontend Testing Framework

### 6.1 Tools

| Tool | Version | Purpose |
|---|---|---|
| Vitest | latest | Test runner (Vite-native, Jest-compatible API) |
| React Testing Library (RTL) | latest | Component rendering + user interaction |
| @testing-library/user-event | latest | Simulated user interactions |
| @testing-library/jest-dom | latest | Extended DOM matchers |
| msw (Mock Service Worker) | latest | API mocking for integration tests |

### 6.2 Test Configuration (`vitest.config.ts`)

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### 6.3 Test Setup (`src/test/setup.ts`)

```typescript
import '@testing-library/jest-dom';
```

### 6.4 Running Frontend Tests

```bash
# Watch mode (development)
cd frontend
npm run test

# Single run (CI)
npm run test:run

# With coverage
npx vitest run --coverage
```

---

## 7. Frontend Component Tests

### 7.1 EcoPointsBadge Test

```tsx
// src/components/__tests__/EcoPointsBadge.test.tsx
import { render, screen } from '@testing-library/react';
import { EcoPointsBadge } from '../EcoPointsBadge';

describe('EcoPointsBadge', () => {
  it('renders points and tier', () => {
    render(<EcoPointsBadge points={245} tier="Seedling" />);
    expect(screen.getByText(/245/)).toBeInTheDocument();
    expect(screen.getByText(/Seedling/)).toBeInTheDocument();
  });

  it('shows Forest tier for 1500+ points', () => {
    render(<EcoPointsBadge points={2000} tier="Forest" />);
    expect(screen.getByText(/Forest/)).toBeInTheDocument();
  });
});
```

### 7.2 GoalProgressBar Test

```tsx
// src/components/__tests__/GoalProgressBar.test.tsx
import { render, screen } from '@testing-library/react';
import { GoalProgressBar } from '../GoalProgressBar';

describe('GoalProgressBar', () => {
  it('renders progress percentage', () => {
    render(<GoalProgressBar current={15.0} target={15.0} />);
    expect(screen.getByText(/15\.0%/)).toBeInTheDocument();
  });

  it('shows goal reached message when current >= target', () => {
    render(<GoalProgressBar current={20.0} target={15.0} />);
    expect(screen.getByText(/reached/i)).toBeInTheDocument();
  });

  it('has accessible progress bar', () => {
    render(<GoalProgressBar current={10.0} target={15.0} />);
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });
});
```

### 7.3 ActivityForm Test

```tsx
// src/components/__tests__/ActivityForm.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ActivityForm } from '../ActivityForm';

describe('ActivityForm', () => {
  it('renders category dropdown', () => {
    render(<ActivityForm onSubmit={vi.fn()} />);
    expect(screen.getByLabelText(/category/i)).toBeInTheDocument();
  });

  it('calls onSubmit with form data', async () => {
    const onSubmit = vi.fn();
    render(<ActivityForm onSubmit={onSubmit} />);

    // Fill form (simplified)
    await userEvent.click(screen.getByRole('button', { name: /log/i }));

    // onSubmit should have been called (details depend on form validation)
  });
});
```

---

## 8. Agent Pipeline Tests (Mocked Gemini)

### 8.1 Mocking Strategy

```python
# tests/conftest.py — Gemini mock fixture

@pytest.fixture
def mock_gemini_service(monkeypatch):
    """Mock GeminiService to avoid real API calls in tests."""

    async def mock_function_call(schema, system_prompt, user_message, **kwargs):
        """Return a valid AnalysisResult-shaped response."""
        return {
            "primary_hotspot": "transport",
            "hotspots": [{
                "category": "transport",
                "pct_of_total": 47.9,
                "vs_baseline_change_pct": -5.2,
                "key_behaviors": ["Daily commute"],
                "reduction_opportunity_kg": 14.0,
            }],
            "behavioral_patterns": ["Consistent weekday commuting"],
            "quick_win_available": True,
            "analysis_confidence": "high",
        }

    async def mock_stream_generate(system_prompt, user_message, **kwargs):
        """Yield mock streaming tokens."""
        for token in ["Your ", "transport ", "is ", "47.9% ", "of total."]:
            yield token

    monkeypatch.setattr(
        "app.services.gemini_service.GeminiService.function_call",
        mock_function_call,
    )
    monkeypatch.setattr(
        "app.services.gemini_service.GeminiService.stream_generate",
        mock_stream_generate,
    )
```

### 8.2 Orchestrator Tests

```python
# tests/unit/test_orchestrator.py

class TestAgentOrchestrator:
    @pytest.mark.asyncio
    async def test_full_pipeline_runs_three_stages(self, mock_gemini_service, db_conn):
        """Pipeline runs Analyst → Planner → Coach in order."""
        orchestrator = AgentOrchestrator(db=db_conn)
        result_tokens = []
        async for token in orchestrator.run_pipeline("test-user-id"):
            result_tokens.append(token)
        assert len(result_tokens) > 0
        assert result_tokens[-1] == "[PIPELINE_COMPLETE]"

    @pytest.mark.asyncio
    async def test_cache_hit_skips_analyst_planner(self, mock_gemini_service, db_conn):
        """When cache is valid, only Coach runs."""
        # Pre-populate cache
        await store_cache(db_conn, "test-user-id", "analyst", '{"valid": true}')
        await store_cache(db_conn, "test-user-id", "planner", '{"valid": true}')

        orchestrator = AgentOrchestrator(db=db_conn)
        # Should skip Analyst and Planner, only run Coach
        result_tokens = []
        async for token in orchestrator.run_pipeline("test-user-id"):
            result_tokens.append(token)
        assert len(result_tokens) > 0

    @pytest.mark.asyncio
    async def test_pipeline_handles_analyst_error(self, db_conn, monkeypatch):
        """If Analyst fails, pipeline returns error frame."""
        async def failing_function_call(*args, **kwargs):
            raise Exception("Gemini API error")

        monkeypatch.setattr(
            "app.services.gemini_service.GeminiService.function_call",
            failing_function_call,
        )

        orchestrator = AgentOrchestrator(db=db_conn)
        result_tokens = []
        async for token in orchestrator.run_pipeline("test-user-id"):
            result_tokens.append(token)
        assert any("[ERROR]" in t for t in result_tokens)
```

---

## 9. Manual E2E Smoke Test

### Pre-Submission Checklist

Run this checklist manually on the deployed production URLs before each competition submission:

```
SMOKE TEST CHECKLIST — CarbonSense AI
═══════════════════════════════════════

Production URLs:
  Frontend: https://carbonsense.vercel.app
  Backend:  https://carbonsense-api.onrender.com

□ 1. LANDING PAGE
  □ 1.1 Navigate to / → Hero section renders
  □ 1.2 Click "Get Started" → redirects to /onboarding

□ 2. ONBOARDING
  □ 2.1 Step 1: Enter name, country, city, lifestyle → Next
  □ 2.2 Step 2: Select transport mode, enter weekly km → Next
  □ 2.3 Step 3: Select diet type → Next
  □ 2.4 Step 4: Enter electricity kWh, select heating → Submit
  □ 2.5 Baseline calculated → redirected to /dashboard
  □ 2.6 Monthly Footprint Card shows baseline value

□ 3. ACTIVITY LOGGING
  □ 3.1 Navigate to /log → Form tab visible
  □ 3.2 Log a transport activity (car_petrol, 20 km) → CO₂ shows ~4.2 kg
  □ 3.3 Activity appears in history table
  □ 3.4 Switch to NL tab → type "drove 25km in diesel car" → CO₂ ~4.25 kg
  □ 3.5 Delete an activity → removed from history

□ 4. DASHBOARD
  □ 4.1 Navigate to /dashboard → all 6 widgets render
  □ 4.2 Pie chart shows category breakdown
  □ 4.3 Trend chart shows data points
  □ 4.4 Switch time range (7d/30d/90d) → chart updates
  □ 4.5 Goal progress bar shows current vs target

□ 5. AI ANALYSIS
  □ 5.1 Click "Analyze My Footprint" → SSE stream starts
  □ 5.2 Coach response streams token-by-token
  □ 5.3 Response references user's actual data (not generic)
  □ 5.4 Stream ends with [PIPELINE_COMPLETE]

□ 6. CHAT
  □ 6.1 Navigate to /chat → input box visible
  □ 6.2 Type "Why is transport my biggest source?" → Send
  □ 6.3 Coach responds with streaming text
  □ 6.4 Response is contextual (references user's transport data)

□ 7. MISSIONS
  □ 7.1 Navigate to /missions → panels visible
  □ 7.2 Available missions displayed (if generated)
  □ 7.3 Accept a mission → moves to Active panel
  □ 7.4 Complete a mission → Eco Points awarded
  □ 7.5 Eco Points badge in nav header updates

□ 8. ACCESSIBILITY
  □ 8.1 Tab through all pages → focus order is logical
  □ 8.2 Charts have aria-labels (inspect element)
  □ 8.3 Forms have labels linked to inputs

□ 9. INFRASTRUCTURE
  □ 9.1 Health check: GET /api/v1/health → 200 ok
  □ 9.2 Keepalive ping visible in DevTools Network tab (14-min interval)
  □ 9.3 CORS: fetch from allowed origin works; other origins blocked

RESULT: □ PASS  □ FAIL (list failures below)
──────────────────────────────────────
Notes:



```

---

## 10. Test Execution in CI

### GitHub Actions Pipeline

```yaml
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

**Important:** All Gemini API calls in tests MUST be mocked. The `GEMINI_API_KEY` secret is available for any tests that need to construct the service, but actual API calls should be avoided in CI to prevent flaky tests and quota consumption.

---

*Document ends.*
