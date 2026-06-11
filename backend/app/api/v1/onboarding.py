import json
import datetime
import aiosqlite
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import AnalyzeRequest, FootprintSummary, UserProfile
from app.db.database import get_db
from app.agents.baseline_agent import BaselineAgent
from app.services.insights_cache import insights_cache

router = APIRouter(tags=["onboarding"])

@router.post("/onboarding/baseline", response_model=FootprintSummary)
async def generate_baseline(req: AnalyzeRequest, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM users WHERE id = ?", (req.user_id,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
        
    profile = UserProfile(**dict(row))
    
    baseline_agent = BaselineAgent()
    estimated = await baseline_agent.estimate(profile)
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await db.execute(
        "UPDATE users SET baseline_footprint_kg = ?, updated_at = ? WHERE id = ?",
        (estimated.total_kg, now, req.user_id)
    )
    
    # Store baseline breakdown in insights_cache
    await insights_cache.set(req.user_id, "baseline", estimated.model_dump_json(), db=db)
    
    # Insert goal if none exists
    async with db.execute(
        "SELECT * FROM goals WHERE user_id = ? AND status = 'active'",
        (req.user_id,)
    ) as cursor:
        existing_goal = await cursor.fetchone()
        
    if not existing_goal:
        deadline = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """
            INSERT INTO goals (user_id, target_reduction_pct, baseline_kg, deadline, status, created_at)
            VALUES (?, 15.0, ?, ?, 'active', ?)
            """,
            (req.user_id, estimated.total_kg, deadline, now)
        )
        
    await db.commit()
    return estimated
