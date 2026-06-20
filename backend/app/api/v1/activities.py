import datetime
import aiosqlite
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import (
    ActivityCreate,
    ActivityResponse,
    NLActivityRequest,
    NLParseResponse,
)
from app.db.database import get_db
from app.services.carbon_engine import calculate_activity_co2
from app.services import gemini_service
from app.services.insights_cache import insights_cache
from app.middleware.rate_limiter import check_rate_limit
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["activities"])

def parse_db_datetime(val: str | datetime.datetime | None) -> datetime.datetime:
    """
    Parse a datetime value returned from the database.

    Args:
        val: A datetime object, ISO-format string, or None.

    Returns:
        A datetime object. Falls back to UTC now on parse failure
        and logs a warning so data integrity issues are visible.
    """
    if isinstance(val, datetime.datetime):
        return val
    if not val:
        return datetime.datetime.utcnow()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(str(val), fmt)
        except ValueError:
            continue
    try:
        return datetime.datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except ValueError:
        logger.warning(
            "parse_db_datetime: unrecognised format %r — using utcnow()", val
        )
        return datetime.datetime.utcnow()

@router.post("/activities", response_model=ActivityResponse)
async def log_activity(activity_in: ActivityCreate, db: aiosqlite.Connection = Depends(get_db)):
    # Verify user exists
    async with db.execute("SELECT id FROM users WHERE id = ?", (activity_in.user_id,)) as cursor:
        user_row = await cursor.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    co2_kg = calculate_activity_co2(activity_in.category, activity_in.type, activity_in.amount)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor = await db.execute(
        """
        INSERT INTO activities (user_id, category, type, amount, unit, co2_kg, source, notes, logged_at)
        VALUES (?, ?, ?, ?, ?, ?, 'form', ?, ?)
        """,
        (
            activity_in.user_id, activity_in.category, activity_in.type,
            activity_in.amount, activity_in.unit, co2_kg, activity_in.notes, now
        )
    )
    activity_id = cursor.lastrowid
    await insights_cache.invalidate(activity_in.user_id, db=db)
    await db.commit()
    
    dt_now = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
    return ActivityResponse(
        activity_id=activity_id,
        user_id=activity_in.user_id,
        category=activity_in.category,
        type=activity_in.type,
        amount=activity_in.amount,
        unit=activity_in.unit,
        co2_kg=co2_kg,
        source="form",
        notes=activity_in.notes,
        logged_at=dt_now
    )

@router.post("/activities/parse-nl", response_model=NLParseResponse)
async def log_nl_activity(req: NLActivityRequest, db: aiosqlite.Connection = Depends(get_db)):
    # Check rate limit
    check_rate_limit(req.user_id, "parse-nl", "rate_limit_nl_rpm")
    
    # Verify user exists
    async with db.execute("SELECT id FROM users WHERE id = ?", (req.user_id,)) as cursor:
        user_row = await cursor.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    parsed = await gemini_service.parse_activity_nl(req.description)
    
    category = parsed.get("category", "transport")
    type_ = parsed.get("type", "car_petrol")
    amount = float(parsed.get("amount", 0.0))
    unit = parsed.get("unit", "km")
    
    co2_kg = calculate_activity_co2(category, type_, amount)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor = await db.execute(
        """
        INSERT INTO activities (user_id, category, type, amount, unit, co2_kg, source, notes, logged_at)
        VALUES (?, ?, ?, ?, ?, ?, 'nl_parse', ?, ?)
        """,
        (
            req.user_id, category, type_, amount, unit, co2_kg, req.description, now
        )
    )
    activity_id = cursor.lastrowid
    await insights_cache.invalidate(req.user_id, db=db)
    await db.commit()
    
    return NLParseResponse(
        parsed=parsed,
        activity_id=activity_id,
        co2_kg=co2_kg
    )

@router.get("/activities/{user_id}")
async def get_activities(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    date: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db)
):
    query = "SELECT * FROM activities WHERE user_id = ?"
    count_query = "SELECT COUNT(*) as total FROM activities WHERE user_id = ?"
    params = [user_id]
    
    if category:
        query += " AND category = ?"
        count_query += " AND category = ?"
        params.append(category.lower().strip())
        
    if date:
        query += " AND DATE(logged_at) = DATE(?)"
        count_query += " AND DATE(logged_at) = DATE(?)"
        params.append(date)
        
    query += " ORDER BY logged_at DESC LIMIT ? OFFSET ?"
    
    offset = (page - 1) * page_size
    params_with_limits = params + [page_size, offset]
    
    async with db.execute(count_query, params) as cursor:
        count_row = await cursor.fetchone()
    total = count_row["total"] if count_row else 0
    
    async with db.execute(query, params_with_limits) as cursor:
        rows = await cursor.fetchall()
        
    activities = []
    for r in rows:
        activities.append(ActivityResponse(
            activity_id=r["id"],
            user_id=r["user_id"],
            category=r["category"],
            type=r["type"],
            amount=r["amount"],
            unit=r["unit"],
            co2_kg=r["co2_kg"],
            source=r["source"],
            notes=r["notes"],
            logged_at=parse_db_datetime(r["logged_at"])
        ))
        
    return {"activities": activities, "total": total}

@router.delete("/activities/{activity_id}")
async def delete_activity(activity_id: int, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT user_id FROM activities WHERE id = ?", (activity_id,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    user_id = row["user_id"]
    await db.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    await insights_cache.invalidate(user_id, db=db)
    await db.commit()
    return {"status": "success", "message": "Activity deleted"}
