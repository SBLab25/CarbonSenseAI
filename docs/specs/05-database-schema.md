# CarbonSense AI — Database Schema

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. Technology Choice and Rationale

**Database:** SQLite via `aiosqlite` (async Python driver)

| Decision Factor | SQLite Fit |
|---|---|
| Zero infrastructure | No external DB server; DB is a file on Render disk |
| Repo-size compliant | DB file not committed (`.gitignore`); created fresh on startup via `init_db()` |
| Single-user MVP | No concurrent multi-process writes needed; UUID-based sessions |
| Performance | Sufficient for < 10,000 rows; dashboard queries < 50ms |
| Async support | `aiosqlite` provides full async API compatible with FastAPI |
| Local development | No DB server to install or start; works immediately |

**Trade-off:** Data is lost on Render redeployment (ephemeral disk). Acceptable for competition scope. V2 migrates to PostgreSQL with persistent volume.

---

## 2. Entity-Relationship Description

```
┌──────────────┐         ┌──────────────────┐
│    users     │         │   activities     │
│──────────────│         │──────────────────│
│ PK id (UUID) │◄───┐    │ PK id (AUTO)     │
│ name         │    │    │ FK user_id ──────┤──── users.id
│ country      │    │    │ category         │
│ city         │    │    │ type             │
│ lifestyle_type│   │    │ amount           │
│ diet_type    │    │    │ unit             │
│ primary_transport│ │   │ co2_kg           │
│ weekly_transport_km││  │ source           │
│ monthly_electricity_kwh││ notes           │
│ heating_type │    │    │ logged_at        │
│ baseline_footprint_kg│ └──────────────────┘
│ monthly_target_reduction_pct│
│ eco_points   │    │    ┌──────────────────┐
│ created_at   │    ├───▶│ insights_cache   │
│ updated_at   │    │    │──────────────────│
└──────────────┘    │    │ PK id (AUTO)     │
                    │    │ FK user_id ──────┤──── users.id
                    │    │ agent_type       │
                    │    │ content_json     │
                    │    │ generated_at     │
                    │    │ valid_until      │
                    │    │ is_valid         │
                    │    └──────────────────┘
                    │
                    │    ┌──────────────────┐
                    ├───▶│    missions      │
                    │    │──────────────────│
                    │    │ PK id (AUTO)     │
                    │    │ FK user_id ──────┤──── users.id
                    │    │ title            │
                    │    │ description      │
                    │    │ category         │
                    │    │ target_reduction_kg│
                    │    │ eco_points_reward│
                    │    │ status           │
                    │    │ created_at       │
                    │    │ accepted_at      │
                    │    │ completed_at     │
                    │    │ deadline         │
                    │    └──────────────────┘
                    │
                    │    ┌──────────────────┐
                    └───▶│     goals        │
                         │──────────────────│
                         │ PK id (AUTO)     │
                         │ FK user_id ──────┤──── users.id
                         │ target_reduction_pct│
                         │ baseline_kg      │
                         │ deadline         │
                         │ status           │
                         │ created_at       │
                         └──────────────────┘
```

**Relationships:**
- `users` → `activities`: one-to-many (one user has many activities)
- `users` → `insights_cache`: one-to-many (cached agent outputs per user)
- `users` → `missions`: one-to-many (missions generated per user)
- `users` → `goals`: one-to-many (user can have multiple goals over time)

All foreign keys reference `users.id` with `ON DELETE CASCADE`.

---

## 3. Table Definitions

```sql
-- =============================================================================
-- TABLE: users
-- Purpose: Session-based user identity and profile data collected during onboarding.
-- The UUID is generated client-side and stored in localStorage.
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id                          TEXT    PRIMARY KEY,          -- UUID v4, generated at onboarding
    name                        TEXT    NOT NULL,             -- User's display name
    country                     TEXT,                         -- Country of residence
    city                        TEXT,                         -- City of residence
    lifestyle_type              TEXT,                         -- urban | suburban | rural
    diet_type                   TEXT,                         -- vegan | vegetarian | mixed | high_meat
    primary_transport           TEXT,                         -- car_petrol | car_diesel | bus | train | etc.
    weekly_transport_km         REAL,                         -- Estimated weekly km traveled
    monthly_electricity_kwh     REAL,                         -- Monthly electricity consumption in kWh
    heating_type                TEXT,                         -- lpg | electric | none
    baseline_footprint_kg       REAL    DEFAULT 0.0,          -- Monthly kg CO₂ from Baseline Agent
    monthly_target_reduction_pct REAL   DEFAULT 15.0,         -- Default reduction goal: 15%
    eco_points                  INTEGER DEFAULT 0,            -- Gamification points balance
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABLE: activities
-- Purpose: Every logged carbon-emitting activity (transport, energy, food, shopping).
-- co2_kg is calculated by the Carbon Engine at log time — never recalculated retroactively.
-- =============================================================================
CREATE TABLE IF NOT EXISTS activities (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category    TEXT        NOT NULL,           -- transport | energy | food | shopping
    type        TEXT        NOT NULL,           -- e.g. car_petrol, beef, electricity
    amount      REAL        NOT NULL,           -- Raw quantity (km, kWh, kg, count)
    unit        TEXT        NOT NULL,           -- km | kWh | kg | item
    co2_kg      REAL        NOT NULL,           -- Calculated at time of logging
    source      TEXT        DEFAULT 'form',     -- form | natural_language
    notes       TEXT,                            -- Optional user notes
    logged_at   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABLE: insights_cache
-- Purpose: Cached agent pipeline outputs (AnalysisResult, PlanResult).
-- Invalidated when user logs a new activity. TTL = 24 hours.
-- =============================================================================
CREATE TABLE IF NOT EXISTS insights_cache (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_type      TEXT        NOT NULL,       -- analyst | planner | coach
    content_json    TEXT        NOT NULL,       -- Serialized Pydantic model as JSON string
    generated_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    valid_until     TIMESTAMP   NOT NULL,       -- generated_at + 24 hours
    is_valid        INTEGER     DEFAULT 1       -- 1 = valid, 0 = invalidated by new activity
);

-- =============================================================================
-- TABLE: missions
-- Purpose: AI-generated sustainability challenges from the Planner Agent.
-- User can accept, complete, or let expire. Completing awards Eco Points.
-- =============================================================================
CREATE TABLE IF NOT EXISTS missions (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_id             TEXT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               TEXT        NOT NULL,           -- Mission display title
    description         TEXT        NOT NULL,           -- Full mission description
    category            TEXT        NOT NULL,           -- transport | energy | food | shopping
    target_reduction_kg REAL,                           -- Estimated CO₂ impact
    eco_points_reward   INTEGER     DEFAULT 100,        -- Points awarded on completion
    status              TEXT        DEFAULT 'pending',  -- pending | active | completed | expired
    created_at          TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    accepted_at         TIMESTAMP,                      -- Set when user accepts
    completed_at        TIMESTAMP,                      -- Set when user completes
    deadline            TIMESTAMP                       -- Set on acceptance (e.g., +7 days)
);

-- =============================================================================
-- TABLE: goals
-- Purpose: User-defined or system-suggested carbon reduction goals.
-- A default goal (15% reduction) is created at onboarding.
-- =============================================================================
CREATE TABLE IF NOT EXISTS goals (
    id                      INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_id                 TEXT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_reduction_pct    REAL        NOT NULL DEFAULT 15.0,   -- Percentage reduction target
    baseline_kg             REAL        NOT NULL,                 -- Baseline footprint when goal was set
    deadline                TIMESTAMP,                            -- Optional goal deadline
    status                  TEXT        DEFAULT 'active',         -- active | achieved | abandoned
    created_at              TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Index Definitions

```sql
-- Activities: fetch user's activity log ordered by date (Dashboard, Activity History)
CREATE INDEX IF NOT EXISTS idx_activities_user_date
    ON activities(user_id, logged_at DESC);

-- Activities: aggregate by category for pie chart breakdown
CREATE INDEX IF NOT EXISTS idx_activities_user_category
    ON activities(user_id, category);

-- Insights cache: check cache validity before running agent pipeline
CREATE INDEX IF NOT EXISTS idx_insights_cache_user
    ON insights_cache(user_id, agent_type, is_valid);

-- Missions: fetch user's missions filtered by status (Mission Center panels)
CREATE INDEX IF NOT EXISTS idx_missions_user_status
    ON missions(user_id, status);
```

**Query Pattern Justifications:**

| Index | Query Pattern | Frequency |
|---|---|---|
| `idx_activities_user_date` | `SELECT * FROM activities WHERE user_id = ? ORDER BY logged_at DESC` | Every page load, every log |
| `idx_activities_user_category` | `SELECT category, SUM(co2_kg) FROM activities WHERE user_id = ? GROUP BY category` | Every dashboard load |
| `idx_insights_cache_user` | `SELECT * FROM insights_cache WHERE user_id = ? AND agent_type = ? AND is_valid = 1` | Every analysis request |
| `idx_missions_user_status` | `SELECT * FROM missions WHERE user_id = ? AND status = ?` | Every missions page load |

---

## 5. Key Query Patterns

### 5.1 Monthly Footprint by Category (Dashboard Pie Chart)

```sql
SELECT
    category,
    SUM(co2_kg) AS total_kg,
    ROUND(SUM(co2_kg) * 100.0 / NULLIF(
        (SELECT SUM(co2_kg) FROM activities
         WHERE user_id = ? AND strftime('%Y-%m', logged_at) = ?), 0
    ), 1) AS pct
FROM activities
WHERE user_id = ?
  AND strftime('%Y-%m', logged_at) = ?
GROUP BY category
ORDER BY total_kg DESC;
```

### 5.2 Daily Trend (Line Chart)

```sql
SELECT
    DATE(logged_at) AS date,
    SUM(co2_kg) AS total_kg
FROM activities
WHERE user_id = ?
  AND logged_at >= DATE('now', ? || ' days')
GROUP BY DATE(logged_at)
ORDER BY date ASC;
```

### 5.3 Check Cache Validity (Before Agent Pipeline)

```sql
SELECT content_json, valid_until, is_valid
FROM insights_cache
WHERE user_id = ?
  AND agent_type = ?
  AND is_valid = 1
  AND valid_until > DATETIME('now')
ORDER BY generated_at DESC
LIMIT 1;
```

### 5.4 Active Missions for User

```sql
SELECT id, title, description, category, target_reduction_kg,
       eco_points_reward, status, deadline,
       JULIANDAY(deadline) - JULIANDAY('now') AS days_remaining
FROM missions
WHERE user_id = ?
  AND status = 'active'
ORDER BY deadline ASC;
```

### 5.5 User Progress vs Baseline

```sql
SELECT
    u.baseline_footprint_kg,
    COALESCE(SUM(a.co2_kg), 0) AS current_month_kg,
    CASE
        WHEN u.baseline_footprint_kg > 0
        THEN ROUND((1.0 - COALESCE(SUM(a.co2_kg), 0) / u.baseline_footprint_kg) * 100, 1)
        ELSE 0
    END AS reduction_pct
FROM users u
LEFT JOIN activities a ON a.user_id = u.id
    AND strftime('%Y-%m', a.logged_at) = strftime('%Y-%m', 'now')
WHERE u.id = ?
GROUP BY u.id;
```

---

## 6. Data Lifecycle

| Table | Created | Updated | Deleted |
|---|---|---|---|
| **users** | POST /users at onboarding Step 4 | PUT /users/{id} for profile edits; POST /onboarding/baseline sets baseline_footprint_kg; mission completion updates eco_points | Never in MVP (UUID-based; data lost on Render redeploy) |
| **activities** | POST /activities (form) or POST /activities/parse-nl (NL) | Never updated — immutable log entries | DELETE /activities/{id} removes entry |
| **insights_cache** | AgentOrchestrator stores agent output after pipeline run | `is_valid` set to 0 on new activity log | Old cache rows accumulate (TTL check prevents stale reads) |
| **missions** | POST /missions/generate creates from Planner output | PUT /missions/{id}/accept sets status, accepted_at, deadline; POST /missions/{id}/complete sets status, completed_at | Never deleted — expired missions stay as history |
| **goals** | Created at onboarding (default 15%) | status updated to 'achieved' or 'abandoned' | Never deleted |

---

## 7. Cache Invalidation Logic

```
FUNCTION check_and_serve_cache(user_id, agent_type):
    row = SELECT content_json, valid_until, is_valid
          FROM insights_cache
          WHERE user_id = {user_id}
            AND agent_type = {agent_type}
          ORDER BY generated_at DESC
          LIMIT 1

    IF row IS NULL:
        RETURN cache_miss    // No cached data exists

    IF row.is_valid == 0:
        RETURN cache_miss    // Invalidated by new activity log

    IF row.valid_until < NOW():
        RETURN cache_miss    // TTL expired (24 hours)

    RETURN cache_hit(row.content_json)


FUNCTION invalidate_on_activity(user_id):
    // Called by POST /activities and POST /activities/parse-nl
    UPDATE insights_cache
    SET is_valid = 0
    WHERE user_id = {user_id}

    // This ensures next analysis runs full pipeline
```

**Key behaviors:**
1. Cache check is a two-condition gate: `is_valid = 1` AND `valid_until > NOW()`
2. Any new activity invalidates ALL agent types for that user
3. Coach Agent output is never cached (always re-generated for freshness)
4. Cache rows are never deleted — old rows are simply never read (most recent valid wins)

---

## 8. Migration Strategy

Migrations are numbered SQL files in `backend/app/db/migrations/`:

```
migrations/
├── 001_initial.sql        ← Full schema creation (all 5 tables + indexes)
├── 002_add_column.sql     ← Example future migration
└── 003_add_table.sql      ← Example future migration
```

**Execution:** `init_db()` runs on FastAPI startup:

```python
async def init_db():
    migrations_dir = Path(__file__).parent / "migrations"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        for migration_file in sorted(migrations_dir.glob("*.sql")):
            sql = migration_file.read_text()
            await db.executescript(sql)
        await db.commit()
```

**Rules:**
- All `CREATE TABLE` uses `IF NOT EXISTS` — migrations are idempotent
- All `CREATE INDEX` uses `IF NOT EXISTS` — safe to re-run
- Migrations run in sorted filename order (001, 002, 003...)
- No down-migration support in MVP (rebuild from scratch on issues)

---

## 9. Constraints and Validation

### Enforced at Database Level

| Constraint | Table | Column | Enforcement |
|---|---|---|---|
| Primary key uniqueness | All tables | `id` | `PRIMARY KEY` |
| Foreign key integrity | activities, insights_cache, missions, goals | `user_id` | `REFERENCES users(id) ON DELETE CASCADE` |
| Non-null required fields | users | `name` | `NOT NULL` |
| Non-null required fields | activities | category, type, amount, unit, co2_kg | `NOT NULL` |
| Non-null required fields | missions | title, description, category | `NOT NULL` |
| Default values | users | eco_points, baseline_footprint_kg, monthly_target_reduction_pct | `DEFAULT` |
| Auto-increment | activities, insights_cache, missions, goals | `id` | `AUTOINCREMENT` |

### Enforced at Application Level (Pydantic)

| Validation | Where | Rule |
|---|---|---|
| UUID format | All user_id fields | Pydantic `str` with UUID regex validator |
| Category enum | ActivityCreate | `category` must be `transport\|energy\|food\|shopping` |
| Unit enum | ActivityCreate | `unit` must be `km\|kWh\|kg\|item` |
| Amount bounds | ActivityCreate | `ge=0`, `le=100000` |
| String length | UserCreate.name | `max_length=100` |
| Diet type enum | UserCreate | `vegan\|vegetarian\|mixed\|high_meat` |
| Mission status enum | Mission | `pending\|active\|completed\|expired` |
| Goal status enum | Goal | `active\|achieved\|abandoned` |

---

## 10. Limitations and V2 Upgrade Path

### Current Limitations

| Limitation | Impact | Acceptable Because |
|---|---|---|
| Ephemeral disk on Render | Data lost on redeploy | Competition demo — fresh start is fine |
| No concurrent write safety | SQLite single-writer lock | Single-user per session; no multi-process writes |
| No full-text search | Cannot search activity notes | Not a required feature for MVP |
| No migration rollback | Cannot undo schema changes | Rebuild-from-scratch is faster for competition |
| Cache rows never cleaned | `insights_cache` grows unbounded | < 10,000 rows expected; no performance impact |

### V2 PostgreSQL Migration Notes

| Step | Action |
|---|---|
| 1. Add PostgreSQL | Replace `aiosqlite` with `asyncpg` or SQLAlchemy async |
| 2. Schema translation | `TEXT PRIMARY KEY` → `UUID PRIMARY KEY DEFAULT gen_random_uuid()` |
| 3. Type changes | `INTEGER DEFAULT 1` → `BOOLEAN DEFAULT TRUE` for `is_valid` |
| 4. Date functions | `strftime('%Y-%m', logged_at)` → `DATE_TRUNC('month', logged_at)` |
| 5. Connection pooling | Add connection pool config (asyncpg pool or SQLAlchemy pool) |
| 6. Migrations tool | Switch from raw SQL files to Alembic for proper up/down migrations |
| 7. Persistent storage | Use Render managed PostgreSQL or Supabase for persistent data |
| 8. Performance | Add JSONB type for `content_json` with GIN index for JSON queries |

---

*Document ends.*
