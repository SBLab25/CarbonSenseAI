import uuid
import datetime
import aiosqlite
from fastapi import APIRouter, HTTPException, Depends, status
from app.config import settings
from app.models.schemas import UserCreate, UserResponse, UserProfile
from app.db.database import get_db

router = APIRouter(tags=["users"])

@router.post("/users", response_model=UserResponse)
async def create_user(user_in: UserCreate, db: aiosqlite.Connection = Depends(get_db)):
    user_id = user_in.id if user_in.id else str(uuid.uuid4())
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    await db.execute(
        """
        INSERT INTO users (
            id, name, country, city, lifestyle_type, diet_type, primary_transport,
            weekly_transport_km, monthly_electricity_kwh, heating_type,
            baseline_footprint_kg, monthly_target_reduction_pct, eco_points, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """,
        (
            user_id, user_in.name, user_in.country, user_in.city,
            user_in.lifestyle_type, user_in.diet_type, user_in.primary_transport,
            user_in.weekly_transport_km, user_in.monthly_electricity_kwh, user_in.heating_type,
            0.0, user_in.monthly_target_reduction_pct, now, now
        )
    )
    await db.commit()
    
    dt_now = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
    return UserResponse(user_id=user_id, created_at=dt_now)

@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user(user_id: str, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(**dict(row))

@router.put("/users/{user_id}", response_model=UserProfile)
async def update_user(user_id: str, user_in: UserCreate, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
        
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await db.execute(
        """
        UPDATE users SET
            name = ?, country = ?, city = ?, lifestyle_type = ?, diet_type = ?,
            primary_transport = ?, weekly_transport_km = ?, monthly_electricity_kwh = ?,
            heating_type = ?, monthly_target_reduction_pct = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            user_in.name, user_in.country, user_in.city, user_in.lifestyle_type,
            user_in.diet_type, user_in.primary_transport, user_in.weekly_transport_km,
            user_in.monthly_electricity_kwh, user_in.heating_type, user_in.monthly_target_reduction_pct,
            now, user_id
        )
    )
    await db.commit()
    
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
        updated = await cursor.fetchone()
    return UserProfile(**dict(updated))

@router.delete("/users/{user_id}/data")
async def delete_user_data(user_id: str, db: aiosqlite.Connection = Depends(get_db)):
    # Verify user exists
    async with db.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete all activities
    await db.execute("DELETE FROM activities WHERE user_id = ?", (user_id,))
    # Delete all missions
    await db.execute("DELETE FROM missions WHERE user_id = ?", (user_id,))
    
    # Update user baseline to 0 and eco points
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await db.execute(
        """
        UPDATE users SET
            baseline_footprint_kg = 0.0,
            eco_points = 0,
            updated_at = ?
        WHERE id = ?
        """,
        (now, user_id)
    )
    
    await db.commit()
    
    # Also need to clear insight caches
    from app.services.insights_cache import insights_cache
    await insights_cache.invalidate(user_id)
    
    return {"status": "success", "message": "All user data wiped successfully."}
