import pytest
import httpx
import aiosqlite
import datetime
from app.main import app
from app.config import settings

@pytest.mark.asyncio
async def test_summary_empty(setup_db, test_user):
    # Clear existing activities
    async with aiosqlite.connect(setup_db) as db:
        await db.execute("DELETE FROM activities WHERE user_id = ?", (test_user,))
        await db.commit()
        
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/carbon/summary/{test_user}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_kg"] == 0.0
        assert data["breakdown"]["transport"]["kg"] == 0.0
        assert data["breakdown"]["energy"]["kg"] == 0.0
        assert data["breakdown"]["food"]["kg"] == 0.0
        assert data["breakdown"]["shopping"]["kg"] == 0.0

@pytest.mark.asyncio
async def test_summary_with_activities(setup_db, test_user):
    # Clear existing activities
    async with aiosqlite.connect(setup_db) as db:
        await db.execute("DELETE FROM activities WHERE user_id = ?", (test_user,))
        await db.commit()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Log food beef activity (27 kg factor)
        await client.post("/api/v1/activities", json={
            "user_id": test_user,
            "category": "food",
            "type": "beef",
            "amount": 2.0,
            "unit": "kg"
        })
        # Log transport petrol car activity (0.21 kg factor)
        await client.post("/api/v1/activities", json={
            "user_id": test_user,
            "category": "transport",
            "type": "car_petrol",
            "amount": 100.0,
            "unit": "km"
        })
        
        response = await client.get(f"/api/v1/carbon/summary/{test_user}")
        assert response.status_code == 200
        data = response.json()
        # total_kg = 54.0 + 21.0 = 75.0
        assert data["total_kg"] == pytest.approx(75.0, rel=0.01)
        assert data["breakdown"]["food"]["kg"] == pytest.approx(54.0, rel=0.01)
        assert data["breakdown"]["transport"]["kg"] == pytest.approx(21.0, rel=0.01)

@pytest.mark.asyncio
async def test_trends_fills_missing_days(setup_db, test_user):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/carbon/trends/{test_user}?days=30")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 30
        
        # Check date sorting is ascending
        dates = [item["date"] for item in data]
        sorted_dates = sorted(dates)
        assert dates == sorted_dates

@pytest.mark.asyncio
async def test_progress_vs_baseline(setup_db, test_user):
    # Set user baseline = 100.0
    async with aiosqlite.connect(setup_db) as db:
        await db.execute("UPDATE users SET baseline_footprint_kg = 100.0 WHERE id = ?", (test_user,))
        await db.execute("DELETE FROM activities WHERE user_id = ?", (test_user,))
        await db.commit()

    # Log activity that equals 80 kg total footprint (e.g. beef = 2.9629 kg or natural gas = 396.0396 kWh)
    # Let's just write an activity directly for testing simplicity or use calculate_activity_co2
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # We can log shopping electronics = 1 item (70kg) + clothing = 1 item (10kg) = 80kg
        await client.post("/api/v1/activities", json={
            "user_id": test_user,
            "category": "shopping",
            "type": "electronics",
            "amount": 1.0,
            "unit": "item"
        })
        await client.post("/api/v1/activities", json={
            "user_id": test_user,
            "category": "shopping",
            "type": "clothing",
            "amount": 1.0,
            "unit": "item"
        })
        
        response = await client.get(f"/api/v1/carbon/progress/{test_user}")
        assert response.status_code == 200
        data = response.json()
        assert data["baseline_kg"] == 100.0
        assert data["current_kg"] == 80.0
        assert data["reduction_pct"] == pytest.approx(20.0, rel=0.01)
