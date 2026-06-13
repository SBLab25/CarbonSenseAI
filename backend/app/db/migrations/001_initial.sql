-- 001_initial.sql

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    city TEXT,
    lifestyle_type TEXT,
    diet_type TEXT,
    primary_transport TEXT,
    weekly_transport_km REAL,
    monthly_electricity_kwh REAL,
    heating_type TEXT,
    baseline_footprint_kg REAL DEFAULT 0.0,
    monthly_target_reduction_pct REAL DEFAULT 15.0,
    eco_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    co2_kg REAL NOT NULL,
    source TEXT DEFAULT 'form',
    notes TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS insights_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    content_json TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP NOT NULL,
    is_valid INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    target_reduction_kg REAL,
    eco_points_reward INTEGER DEFAULT 100,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    completed_at TIMESTAMP,
    deadline TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    target_reduction_pct REAL NOT NULL DEFAULT 15.0,
    baseline_kg REAL NOT NULL,
    deadline TIMESTAMP,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_activities_user_date ON activities (user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_activities_user_category ON activities (user_id, category);
CREATE INDEX IF NOT EXISTS idx_insights_cache_user ON insights_cache (user_id);
CREATE INDEX IF NOT EXISTS idx_missions_user_status ON missions (user_id, status);
