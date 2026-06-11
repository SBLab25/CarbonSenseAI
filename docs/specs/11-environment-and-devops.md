# CarbonSense AI — Environment & DevOps

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. Environment Overview

| Environment | Purpose | URL Pattern | Platform |
|---|---|---|---|
| **Local** | Development and testing | `localhost:5173` (frontend), `localhost:8000` (backend) | Developer machine |
| **CI** | Automated testing on push | — (no deploy) | GitHub Actions |
| **Production** | Competition submission and demo | `carbonsense.vercel.app` (frontend), `carbonsense-api.onrender.com` (backend) | Vercel + Render |

---

## 2. Local Development Setup

### 2.1 Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Node.js | 20.x LTS | Frontend runtime |
| Python | 3.11 | Backend runtime |
| npm | 10.x | Frontend package manager |
| pip | 24.x | Python package installer |
| Git | 2.40+ | Version control |

### 2.2 Initial Setup Commands

```bash
# 1. Clone repository
git clone https://github.com/<username>/carbonsense-ai.git
cd carbonsense-ai

# 2. Backend setup
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt

# 3. Backend environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY from Google AI Studio

# 4. Start backend
uvicorn app.main:app --reload --port 8000
# Verify: http://localhost:8000/api/v1/health → {"status":"ok"}

# 5. Frontend setup (new terminal)
cd frontend
npm install

# 6. Frontend environment
cp .env.example .env
# .env should contain: VITE_API_URL=http://localhost:8000

# 7. Start frontend
npm run dev
# Verify: http://localhost:5173 → Landing page renders
```

### 2.3 Local Environment Variables

**Backend (`backend/.env`):**

```env
GEMINI_API_KEY=your_key_from_google_ai_studio
DATABASE_URL=./carbonsense.db
ALLOWED_ORIGINS=http://localhost:5173
APP_ENV=development
RATE_LIMIT_CHAT_RPM=10
RATE_LIMIT_ANALYZE_RPH=3
RATE_LIMIT_NL_RPM=20
```

**Frontend (`frontend/.env`):**

```env
VITE_API_URL=http://localhost:8000
```

### 2.4 Development Workflow

```
Terminal 1 (Backend):
  cd backend
  source .venv/bin/activate       # (or .venv\Scripts\activate on Windows)
  uvicorn app.main:app --reload --port 8000

Terminal 2 (Frontend):
  cd frontend
  npm run dev                     # Vite dev server on :5173

Terminal 3 (Tests — as needed):
  cd backend && pytest tests/ -v --cov=app
  cd frontend && npm run test
```

### 2.5 Hot Reload Behavior

| Stack | Mechanism | What Triggers Reload |
|---|---|---|
| Backend | `--reload` flag (uvicorn watchfiles) | Any `.py` file change in `backend/app/` |
| Frontend | Vite HMR (Hot Module Replacement) | Any `.tsx`, `.ts`, `.css` file change in `frontend/src/` |
| Database | Auto-init on startup (`init_db()`) | Migrations run on every FastAPI startup |

---

## 3. Backend Configuration (`config.py`)

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All configuration loaded from environment variables.
    Pydantic validates types and enforces required fields.
    """
    # Required — app refuses to start without
    gemini_api_key: str

    # Database
    database_url: str = "./carbonsense.db"

    # CORS — comma-separated allowed origins
    allowed_origins: list[str] = ["http://localhost:5173"]

    # Rate limits
    rate_limit_chat_rpm: int = 10
    rate_limit_analyze_rph: int = 3
    rate_limit_nl_rpm: int = 20

    # Environment
    app_env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

**Key behaviors:**
- `gemini_api_key` has no default — app crashes on startup if missing (intentional)
- `allowed_origins` is parsed from `ALLOWED_ORIGINS=http://localhost:5173,https://carbonsense.vercel.app`
- `Config.env_file = ".env"` — pydantic-settings auto-loads the `.env` file

---

## 4. CI/CD Pipeline

### 4.1 GitHub Actions Configuration

```yaml
# .github/workflows/ci.yml
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
        with:
          python-version: "3.11"
      - name: Install backend dependencies
        run: pip install -r backend/requirements.txt
      - name: Run backend tests
        run: pytest backend/tests/ -v --cov=app --cov-report=term-missing
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          DATABASE_URL: ./test.db
          ALLOWED_ORIGINS: http://localhost:5173

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install frontend dependencies
        run: npm ci
        working-directory: frontend
      - name: Run frontend tests
        run: npm run test:run
        working-directory: frontend

  frontend-build:
    runs-on: ubuntu-latest
    needs: frontend-test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install dependencies
        run: npm ci
        working-directory: frontend
      - name: Build check
        run: npm run build
        working-directory: frontend
        env:
          VITE_API_URL: https://carbonsense-api.onrender.com
```

### 4.2 GitHub Secrets

| Secret Name | Where Set | Used By |
|---|---|---|
| `GEMINI_API_KEY` | GitHub → Settings → Secrets | `backend-test` job |

### 4.3 CI Pipeline Diagram

```
Push to main
       │
       ├───────────────────┬────────────────────┐
       ▼                   ▼                    ▼
 backend-test        frontend-test        (parallel)
   │ pytest            │ vitest
   │ --cov             │ npm run test:run
   ▼                   ▼
  PASS/FAIL          PASS/FAIL
                       │
                       ▼
                 frontend-build    (runs after frontend-test)
                   │ npm run build
                   ▼
                  PASS/FAIL
```

---

## 5. Frontend Deployment (Vercel)

### 5.1 Setup Steps

1. Push repository to GitHub
2. Login to [vercel.com](https://vercel.com) → **New Project** → Import GitHub repo
3. Set **Root Directory** to `frontend`
4. Vercel auto-detects Vite — leave build settings as default:
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`
5. Add environment variable:
   - **Name:** `VITE_API_URL`
   - **Value:** `https://carbonsense-api.onrender.com`
6. Click **Deploy**
7. Note production URL: `https://carbonsense.vercel.app` (or Vercel-assigned URL)

### 5.2 Vercel Build Settings

| Setting | Value |
|---|---|
| Framework | Vite |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Node Version | 20.x |

### 5.3 Vercel Behavior

| Feature | Detail |
|---|---|
| **Auto-deploy** | Every push to `main` triggers a new deployment |
| **CDN** | Static assets served from Vercel's global edge network |
| **Preview** | Pull requests get preview deployments (not needed — single branch) |
| **SPA routing** | Vite + React Router handles client-side routing; Vercel serves `index.html` for all routes |

### 5.4 SPA Routing Configuration

Create `frontend/vercel.json` to ensure all routes serve `index.html`:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## 6. Backend Deployment (Render)

### 6.1 Setup Steps

1. Login to [render.com](https://render.com) → **New** → **Web Service**
2. Connect GitHub repository
3. Configure:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3.11
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set **Health Check Path:** `/api/v1/health`
5. Add environment variables:
   - `GEMINI_API_KEY` = your Google AI Studio key
   - `DATABASE_URL` = `./carbonsense.db`
   - `ALLOWED_ORIGINS` = `https://carbonsense.vercel.app`
   - `APP_ENV` = `production`
6. Click **Deploy**
7. Note service URL: `https://carbonsense-api.onrender.com`
8. Go back to Vercel → paste URL as `VITE_API_URL`

### 6.2 Render Configuration

| Setting | Value |
|---|---|
| Service Type | Web Service |
| Runtime | Python 3.11 |
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/v1/health` |
| Plan | Free |

### 6.3 Render Free Tier Constraints

| Constraint | Detail | Mitigation |
|---|---|---|
| 512 MB RAM | Limited memory for Python process | SQLite is lightweight; no ORM overhead |
| Ephemeral disk | Data lost on redeploy | Acceptable for competition; seed script for demo data |
| Spin-down after 15 min | Service sleeps after 15 minutes of inactivity | Frontend keepalive ping every 14 minutes |
| Cold start ~30s | First request after spin-down takes ~30s | Keepalive prevents spin-down during demo |

### 6.4 Keepalive Implementation

**Frontend (`frontend/src/lib/keepalive.ts`):**

```typescript
const PING_INTERVAL_MS = 14 * 60 * 1000; // 14 minutes

export function startKeepalive(): () => void {
  const ping = () =>
    fetch(`${import.meta.env.VITE_API_URL}/api/v1/health`).catch(() => {});

  ping(); // immediate ping on app load
  const interval = setInterval(ping, PING_INTERVAL_MS);
  return () => clearInterval(interval); // cleanup for useEffect
}
```

**Frontend (`frontend/src/App.tsx`):**

```typescript
useEffect(() => {
  const cleanup = startKeepalive();
  return cleanup;
}, []);
```

**How it works:** As long as any browser tab has the CarbonSense app open, the backend receives a `/health` ping every 14 minutes, preventing Render from spinning down the service.

---

## 7. Environment Variables Summary

### 7.1 Full Variable Reference

| Variable | Required | Default | Platform | Description |
|---|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Backend | Google AI Studio API key for Gemini 1.5 Flash |
| `DATABASE_URL` | No | `./carbonsense.db` | Backend | Path to SQLite database file |
| `ALLOWED_ORIGINS` | No | `http://localhost:5173` | Backend | Comma-separated CORS allowed origins |
| `APP_ENV` | No | `development` | Backend | Environment identifier |
| `RATE_LIMIT_CHAT_RPM` | No | `10` | Backend | Chat endpoint: max requests per minute per user |
| `RATE_LIMIT_ANALYZE_RPH` | No | `3` | Backend | Analyze endpoint: max requests per hour per user |
| `RATE_LIMIT_NL_RPM` | No | `20` | Backend | NL parse endpoint: max requests per minute per user |
| `VITE_API_URL` | Yes | — | Frontend | Backend API base URL |

### 7.2 Per-Environment Values

| Variable | Local | CI | Production |
|---|---|---|---|
| `GEMINI_API_KEY` | `.env` | GitHub Secret | Render env var |
| `DATABASE_URL` | `./carbonsense.db` | `./test.db` | `./carbonsense.db` |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | `http://localhost:5173` | `https://carbonsense.vercel.app` |
| `APP_ENV` | `development` | `development` | `production` |
| `VITE_API_URL` | `http://localhost:8000` | — (not needed) | `https://carbonsense-api.onrender.com` |

---

## 8. Database Management

### 8.1 Local Development

```bash
# Database is auto-created on first FastAPI startup
# Location: backend/carbonsense.db

# To reset database (delete and recreate):
rm backend/carbonsense.db
# Restart uvicorn → init_db() recreates all tables

# To inspect database:
sqlite3 backend/carbonsense.db
.tables              # List all tables
.schema users        # Show CREATE TABLE for users
SELECT COUNT(*) FROM activities;
.quit
```

### 8.2 Production (Render)

```
On Render:
- Database file: ./carbonsense.db (ephemeral disk)
- Auto-created on service start via init_db()
- Data persists between requests but is LOST on redeploy
- No backup mechanism (competition scope)
```

### 8.3 CI Testing

```python
# conftest.py creates a temp SQLite per test session:
@pytest.fixture(autouse=True, scope="session")
async def setup_test_db(tmp_path_factory, monkeypatch):
    tmp_db = str(tmp_path_factory.mktemp("db") / "test.db")
    monkeypatch.setenv("DATABASE_URL", tmp_db)
    await init_db()
```

---

## 9. Logging Strategy

### 9.1 Backend Logging

```python
import logging

# Configure in main.py
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
```

**Log levels by module:**

| Module | Level | What Gets Logged |
|---|---|---|
| `api/v1/*` | INFO | Request method + path + status code |
| `services/gemini_service` | INFO | Gemini API call initiated + duration |
| `services/carbon_engine` | WARNING | Unknown category/type fallback to 0.0 |
| `agents/*` | INFO | Agent started, output received, validation passed |
| `services/agent_orchestrator` | INFO | Pipeline stage transitions, cache hit/miss |
| `middleware/rate_limiter` | WARNING | Rate limit exceeded events |
| Global exception handler | ERROR | Full stack trace + error detail (never to frontend) |

### 9.2 Structured Log Examples

```
2026-06-09 10:30:15 [INFO] api.v1.activities: POST /activities user=a1b2c3d4 category=transport co2_kg=4.2
2026-06-09 10:30:15 [INFO] services.gemini_service: function_call initiated model=gemini-1.5-flash duration_ms=842
2026-06-09 10:30:16 [INFO] services.agent_orchestrator: Pipeline stage=analyst cache=MISS user=a1b2c3d4
2026-06-09 10:30:18 [WARNING] services.carbon_engine: Unknown activity type: rocket_ship in transport
2026-06-09 10:30:20 [ERROR] main: GeminiError: Gemini API returned 500: internal error
```

---

## 10. Monitoring (Production)

### 10.1 Health Check

```
Render health check:
  Path: GET /api/v1/health
  Expected: 200 {"status":"ok","timestamp":"..."}
  Interval: Render default (30s)
  Failure: Service marked unhealthy → restart

Frontend keepalive:
  Path: GET /api/v1/health
  Interval: Every 14 minutes
  Purpose: Prevent Render free-tier spin-down
```

### 10.2 Vercel Analytics

Vercel provides built-in analytics for the frontend:
- Web Vitals (LCP, FID, CLS)
- Page views and navigation patterns
- Edge function execution time (N/A — static SPA)

### 10.3 Error Tracking

No dedicated error tracking service in MVP (competition scope). Errors are logged to:
- **Backend:** `stdout` (captured by Render logs dashboard)
- **Frontend:** Browser console (developer inspection)

**V2 upgrade:** Add Sentry for both frontend and backend error tracking.

---

## 11. Docker Development (Optional)

### 11.1 Backend Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 11.2 Docker Compose (Full Stack)

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DATABASE_URL=./carbonsense.db
      - ALLOWED_ORIGINS=http://localhost:5173
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
```

**Note:** Docker is optional for local development. Direct `uvicorn` + `npm run dev` is simpler and recommended for the competition timeline.

---

*Document ends.*
