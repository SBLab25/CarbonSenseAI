import os
import json
import aiosqlite
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.config import settings
from app.models.schemas import UserProfile, FootprintSummary, UserContext

async def init_db():
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

async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with aiosqlite.connect(settings.database_url, timeout=30.0) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        yield db

async def get_user_context(user_id: str) -> UserContext:
    async with aiosqlite.connect(settings.database_url, timeout=30.0) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        
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
        # In SQLite, we can get the current year-month
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
