import os
import json
import aiosqlite
import psycopg
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.config import settings
from app.models.schemas import UserProfile, FootprintSummary, UserContext

# SQL translation logic
def translate_query(query: str, is_postgres: bool) -> str:
    if not is_postgres:
        return query
    
    # SQLite strftime -> Postgres to_char
    query = query.replace("strftime('%Y-%m', logged_at)", "to_char(logged_at, 'YYYY-MM')")
    query = query.replace("strftime('%Y-%m', a.logged_at)", "to_char(a.logged_at, 'YYYY-MM')")
    query = query.replace("strftime('%Y-%m', 'now')", "to_char(CURRENT_TIMESTAMP, 'YYYY-MM')")
    
    # SQLite DATE -> Postgres date
    query = query.replace("DATE(logged_at)", "logged_at::date")
    query = query.replace("DATE('now', ? || ' days')", "CURRENT_DATE + (%s || ' days')::interval")
    query = query.replace("DATE('now', %s || ' days')", "CURRENT_DATE + (%s || ' days')::interval")
    
    # SQLite JULIANDAY -> Postgres extract epoch/days
    query = query.replace("JULIANDAY(deadline) - JULIANDAY('now')", "EXTRACT(DAY FROM (deadline - CURRENT_TIMESTAMP))")
    
    # Replace SQLite ? with psycopg %s
    query = query.replace("?", "%s")
    
    return query

class PostgresCursorWrapper:
    def __init__(self, cur, lastrowid=None):
        self._cur = cur
        self.lastrowid = lastrowid

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cur.close()

    async def fetchone(self):
        row = await self._cur.fetchone()
        return dict(row) if row is not None else None

    async def fetchall(self):
        rows = await self._cur.fetchall()
        return [dict(r) for r in rows]

class AwaitableCursorContext:
    def __init__(self, conn, query: str, params=None):
        self._conn = conn
        self._query = query
        self._params = params
        self._cur = None

    def __await__(self):
        async def _execute():
            query_upper = self._query.strip().upper()
            inserted_id = None
            modified_query = self._query
            if query_upper.startswith("INSERT ") and "RETURNING" not in query_upper:
                modified_query = self._query.rstrip(" ;") + " RETURNING id"
                
            cur = self._conn.cursor(row_factory=dict_row)
            await cur.execute(modified_query, self._params)
            
            if query_upper.startswith("INSERT ") and "RETURNING" not in query_upper:
                row = await cur.fetchone()
                if row:
                    inserted_id = list(row.values())[0]
            
            return PostgresCursorWrapper(cur, lastrowid=inserted_id)
        return _execute().__await__()

    async def __aenter__(self):
        query_upper = self._query.strip().upper()
        inserted_id = None
        modified_query = self._query
        if query_upper.startswith("INSERT ") and "RETURNING" not in query_upper:
            modified_query = self._query.rstrip(" ;") + " RETURNING id"
            
        self._cur = self._conn.cursor(row_factory=dict_row)
        await self._cur.execute(modified_query, self._params)
        
        if query_upper.startswith("INSERT ") and "RETURNING" not in query_upper:
            row = await self._cur.fetchone()
            if row:
                inserted_id = list(row.values())[0]
                
        return PostgresCursorWrapper(self._cur, lastrowid=inserted_id)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._cur:
            await self._cur.close()

class PostgresConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, query: str, params=None):
        translated = translate_query(query, is_postgres=True)
        return AwaitableCursorContext(self._conn, translated, params)

    async def executescript(self, sql_script: str):
        translated = translate_query(sql_script, is_postgres=True)
        async with self._conn.cursor() as cur:
            await cur.execute(translated)

    async def commit(self):
        await self._conn.commit()

    async def close(self):
        await self._conn.close()

def is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql://") or url.startswith("postgres://")

@asynccontextmanager
async def get_db_context():
    if is_postgres_url(settings.database_url):
        conn = await psycopg.AsyncConnection.connect(settings.database_url)
        try:
            yield PostgresConnectionWrapper(conn)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(settings.database_url, timeout=30.0) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row
            yield db

async def init_db():
    if is_postgres_url(settings.database_url):
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        if not os.path.exists(migrations_dir):
            return
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])
        
        async with await psycopg.AsyncConnection.connect(settings.database_url) as conn:
            for file in migration_files:
                file_path = os.path.join(migrations_dir, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    sql = f.read()
                statements = sql.split(";")
                async with conn.cursor() as cur:
                    for statement in statements:
                        clean = statement.strip()
                        if not clean or clean.upper().startswith("PRAGMA"):
                            continue
                        translated = translate_query(clean, is_postgres=True)
                        try:
                            await cur.execute(translated)
                        except Exception:
                            # Ignore if tables already exist
                            pass
            await conn.commit()
    else:
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        if not os.path.exists(migrations_dir):
            return
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])
        async with aiosqlite.connect(settings.database_url, timeout=30.0) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            for file in migration_files:
                file_path = os.path.join(migrations_dir, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    sql = f.read()
                await db.executescript(sql)
            await db.commit()

async def get_db() -> AsyncGenerator[Any, None]:
    if is_postgres_url(settings.database_url):
        conn = await psycopg.AsyncConnection.connect(settings.database_url)
        try:
            yield PostgresConnectionWrapper(conn)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(settings.database_url, timeout=30.0) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row
            yield db

async def get_user_context(user_id: str) -> UserContext:
    async with get_db_context() as db:
        # 1. Fetch user profile
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()
        if not user_row:
            raise ValueError(f"User not found: {user_id}")
            
        profile_dict = dict(user_row)
        profile = UserProfile(**profile_dict)
        
        # 2. Get active goal
        async with db.execute(
            "SELECT * FROM goals WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            goal_row = await cursor.fetchone()
        active_goal = dict(goal_row) if goal_row else None
        
        # 3. Get recent activities (e.g. last 50)
        async with db.execute(
            "SELECT * FROM activities WHERE user_id = ? ORDER BY logged_at DESC LIMIT 50",
            (user_id,)
        ) as cursor:
            activities_rows = await cursor.fetchall()
        recent_activities = [dict(row) for row in activities_rows]
        
        # 4. Get current month activities for footprint summary
        async with db.execute(
            "SELECT * FROM activities WHERE user_id = ? AND strftime('%Y-%m', logged_at) = strftime('%Y-%m', 'now')",
            (user_id,)
        ) as cursor:
            month_activities_rows = await cursor.fetchall()
        month_activities = [dict(row) for row in month_activities_rows]
        
        # 5. Calculate current footprint summary
        from app.services.carbon_engine import calculate_monthly_summary, calculate_progress
        current_footprint = calculate_monthly_summary(month_activities, profile.baseline_footprint_kg)
        
        # 6. Fetch baseline footprint from insights cache if present
        async with db.execute(
            "SELECT content_json FROM insights_cache WHERE user_id = ? AND agent_type = 'baseline' AND is_valid = 1 ORDER BY generated_at DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            cache_row = await cursor.fetchone()
            
        if cache_row:
            baseline_data = json.loads(cache_row['content_json'])
            baseline_footprint = FootprintSummary(**baseline_data)
        else:
            # Fallback: estimate from profile baseline_footprint_kg
            total = profile.baseline_footprint_kg
            baseline_footprint = FootprintSummary(
                total_kg=total,
                transport_kg=total * 0.3,
                energy_kg=total * 0.4,
                food_kg=total * 0.2,
                shopping_kg=total * 0.1
            )
            
        progress_pct = calculate_progress(current_footprint.total_kg, profile.baseline_footprint_kg)
        
        return UserContext(
            user_id=user_id,
            profile=profile,
            baseline_footprint=baseline_footprint,
            current_footprint=current_footprint,
            recent_activities=recent_activities,
            active_goal=active_goal,
            progress_pct=progress_pct
        )
