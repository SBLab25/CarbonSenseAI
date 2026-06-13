import datetime
import aiosqlite
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import AnalyzeRequest, PlanResult
from app.db.database import get_db
from app.services.insights_cache import insights_cache

router = APIRouter(tags=["missions"])

@router.get("/missions/{user_id}")
async def get_user_missions(user_id: str, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM missions WHERE user_id = ?", (user_id,)) as cursor:
        rows = await cursor.fetchall()
        
    missions = [dict(row) for row in rows]
    
    return {
        "pending": [m for m in missions if m["status"] == "pending"],
        "active": [m for m in missions if m["status"] == "active"],
        "completed": [m for m in missions if m["status"] == "completed"]
    }

@router.post("/missions/generate")
async def generate_missions(req: AnalyzeRequest, db: aiosqlite.Connection = Depends(get_db)):
    planner_json = await insights_cache.get(req.user_id, "planner", db=db)
    if not planner_json:
        raise HTTPException(
            status_code=400,
            detail="Complete an AI analysis first to get personalized missions."
        )
        
    plan = PlanResult.model_validate_json(planner_json)
    
    new_missions = []
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for s in plan.strategies:
        if s.mission_type:
            # Prevent duplicates
            async with db.execute(
                "SELECT id FROM missions WHERE user_id = ? AND title = ?",
                (req.user_id, s.title)
            ) as cursor:
                exists = await cursor.fetchone()
            if exists:
                continue
                
            difficulty = s.difficulty.lower().strip()
            reward = 100
            if difficulty == "medium":
                reward = 200
            elif difficulty == "hard":
                reward = 300
                
            cursor = await db.execute(
                """
                INSERT INTO missions (user_id, title, description, category, target_reduction_kg, eco_points_reward, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (req.user_id, s.title, s.action, s.category, s.monthly_saving_kg, reward, now)
            )
            mission_id = cursor.lastrowid
            
            new_missions.append({
                "id": mission_id,
                "user_id": req.user_id,
                "title": s.title,
                "description": s.action,
                "category": s.category,
                "target_reduction_kg": s.monthly_saving_kg,
                "eco_points_reward": reward,
                "status": "pending",
                "created_at": now
            })
            
    await db.commit()
    return new_missions

@router.put("/missions/{mission_id}/accept")
async def accept_mission(mission_id: int, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM missions WHERE id = ?", (mission_id,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    mission = dict(row)
    if mission["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Mission cannot be accepted from status: {mission['status']}")
        
    now_dt = datetime.datetime.now()
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    deadline = (now_dt + datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    
    await db.execute(
        "UPDATE missions SET status = 'active', accepted_at = ?, deadline = ? WHERE id = ?",
        (now, deadline, mission_id)
    )
    await db.commit()
    
    return {"status": "success", "message": "Mission accepted"}

@router.post("/missions/{mission_id}/complete")
async def complete_mission(mission_id: int, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM missions WHERE id = ?", (mission_id,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    mission = dict(row)
    if mission["status"] == "completed":
        return {"status": "success", "message": "Mission already completed"}
        
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    await db.execute(
        "UPDATE missions SET status = 'completed', completed_at = ? WHERE id = ?",
        (now, mission_id)
    )
    
    await db.execute(
        "UPDATE users SET eco_points = eco_points + ? WHERE id = ?",
        (mission["eco_points_reward"], mission["user_id"])
    )
    
    # Log the reduction activity
    co2_saved = float(mission["target_reduction_kg"] or 0.0)
    await db.execute(
        """
        INSERT INTO activities (user_id, category, type, amount, unit, co2_kg, source, notes, logged_at)
        VALUES (?, ?, ?, 1.0, 'mission', ?, 'mission', ?, ?)
        """,
        (
            mission["user_id"],
            mission["category"],
            f"Completed Mission: {mission['title']}",
            -co2_saved,
            f"Eco Reward: +{mission['eco_points_reward']} Points",
            now
        )
    )
    
    await insights_cache.invalidate(mission["user_id"], db=db)
    await db.commit()
    
    return {"status": "success", "message": "Mission completed, points awarded and activity logged"}
