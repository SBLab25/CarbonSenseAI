import pytest
import httpx
import aiosqlite
from app.main import app
from app.config import settings

@pytest.mark.asyncio
async def test_create_user(setup_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Jane Doe",
            "country": "India",
            "city": "Mumbai",
            "lifestyle_type": "suburban",
            "diet_type": "mixed",
            "primary_transport": "bus",
            "weekly_transport_km": 120.0,
            "monthly_electricity_kwh": 150.0,
            "heating_type": "none",
            "monthly_target_reduction_pct": 15.0
        }
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "created_at" in data

@pytest.mark.asyncio
async def test_baseline_sets_footprint(setup_db, test_user, mock_gemini):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "user_id": test_user
        }
        response = await client.post("/api/v1/onboarding/baseline", json=payload)
        assert response.status_code == 200
        
        # Verify user baseline footprint was updated in db
        async with aiosqlite.connect(setup_db) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT baseline_footprint_kg FROM users WHERE id = ?", (test_user,)) as cursor:
                row = await cursor.fetchone()
            assert row is not None
            # Baseline footprint estimated by mock baseline agent is 180.0
            assert row["baseline_footprint_kg"] == 180.0
            
            # Verify a goal row was created in db
            async with db.execute("SELECT * FROM goals WHERE user_id = ?", (test_user,)) as cursor:
                goal_row = await cursor.fetchone()
            assert goal_row is not None
            assert goal_row["baseline_kg"] == 180.0
