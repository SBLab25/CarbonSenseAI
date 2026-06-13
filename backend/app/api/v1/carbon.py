import datetime
import aiosqlite
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    CarbonSummary,
    CarbonTrend,
    ProgressReport,
    UserProfile,
)
from app.db.database import get_db
from app.services.carbon_engine import (
    calculate_monthly_summary,
    calculate_category_breakdown,
    calculate_trend,
    calculate_progress,
    get_vs_india_average,
)

router = APIRouter(tags=["carbon"])

@router.get("/carbon/summary/{user_id}", response_model=CarbonSummary)
async def get_carbon_summary(user_id: str, db: aiosqlite.Connection = Depends(get_db)):
    # Verify user
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
        user_row = await cursor.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
    
    baseline_kg = user_row["baseline_footprint_kg"]
    
    # Get current month activities
    async with db.execute(
        "SELECT * FROM activities WHERE user_id = ? AND strftime('%Y-%m', logged_at) = strftime('%Y-%m', 'now')",
        (user_id,)
    ) as cursor:
        rows = await cursor.fetchall()
    activities = [dict(row) for row in rows]
    
    summary = calculate_monthly_summary(activities, baseline_kg)
    breakdown = calculate_category_breakdown(summary)
    vs_india = get_vs_india_average(summary.total_kg)
    progress_pct = calculate_progress(summary.total_kg, baseline_kg)
    
    now = datetime.datetime.now()
    period = now.strftime("%B %Y")
    
    return CarbonSummary(
        user_id=user_id,
        period=period,
        total_kg=summary.total_kg,
        baseline_kg=baseline_kg,
        reduction_pct=progress_pct,
        breakdown=breakdown,
        vs_india_average_pct=vs_india
    )

@router.get("/carbon/trends/{user_id}", response_model=list[CarbonTrend])
async def get_carbon_trends(user_id: str, days: int = 30, db: aiosqlite.Connection = Depends(get_db)):
    # Verify user
    async with db.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
        user_row = await cursor.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    async with db.execute(
        "SELECT DATE(logged_at) as date_str, SUM(co2_kg) as total_kg FROM activities WHERE user_id = ? GROUP BY DATE(logged_at)",
        (user_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        
    daily_totals = {}
    for r in rows:
        if r["date_str"]:
            daily_totals[r["date_str"]] = r["total_kg"]
            
    trends = calculate_trend(daily_totals, days)
    return trends

@router.get("/carbon/progress/{user_id}", response_model=ProgressReport)
async def get_carbon_progress(user_id: str, db: aiosqlite.Connection = Depends(get_db)):
    # Verify user
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
        user_row = await cursor.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
        
    baseline_kg = user_row["baseline_footprint_kg"]
    
    # Get current month sum
    async with db.execute(
        "SELECT SUM(co2_kg) as total FROM activities WHERE user_id = ? AND strftime('%Y-%m', logged_at) = strftime('%Y-%m', 'now')",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
    current_kg = row["total"] if row and row["total"] is not None else 0.0
    
    progress_pct = calculate_progress(current_kg, baseline_kg)
    
    return ProgressReport(
        user_id=user_id,
        baseline_kg=baseline_kg,
        current_kg=current_kg,
        reduction_pct=progress_pct
    )
