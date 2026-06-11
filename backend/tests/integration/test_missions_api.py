import pytest
import httpx
import aiosqlite
from app.main import app
from app.services.insights_cache import insights_cache
from app.config import settings

@pytest.mark.asyncio
async def test_get_missions_empty(setup_db, test_user):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/missions/{test_user}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["pending"]) == 0
        assert len(data["active"]) == 0
        assert len(data["completed"]) == 0

@pytest.mark.asyncio
async def test_generate_missions_without_cache(setup_db, test_user):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"user_id": test_user}
        response = await client.post("/api/v1/missions/generate", json=payload)
        assert response.status_code == 400
        assert "Complete an AI analysis first" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_accept_complete_mission_flow(setup_db, test_user):
    # Set cache
    plan_json = '{"strategies": [{"title": "Carpool to work", "action": "Carpool twice a week", "category": "transport", "monthly_saving_kg": 30.0, "difficulty": "easy", "timeframe_days": 7, "mission_type": "carpool"}], "total_potential_saving_kg": 30.0, "recommended_goal_pct": 15.0, "thirty_day_focus": "Transport"}'
    await insights_cache.set(test_user, "planner", plan_json)
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Generate missions
        gen_res = await client.post("/api/v1/missions/generate", json={"user_id": test_user})
        assert gen_res.status_code == 200
        missions = gen_res.json()
        assert len(missions) == 1
        mission_id = missions[0]["id"]
        
        # Verify it shows in pending
        get_res = await client.get(f"/api/v1/missions/{test_user}")
        assert len(get_res.json()["pending"]) == 1
        
        # 2. Accept mission
        accept_res = await client.put(f"/api/v1/missions/{mission_id}/accept")
        assert accept_res.status_code == 200
        
        # Verify it is active
        get_res2 = await client.get(f"/api/v1/missions/{test_user}")
        assert len(get_res2.json()["active"]) == 1
        assert len(get_res2.json()["pending"]) == 0
        
        # 3. Complete mission
        complete_res = await client.post(f"/api/v1/missions/{mission_id}/complete")
        assert complete_res.status_code == 200
        
        # Verify it is completed
        get_res3 = await client.get(f"/api/v1/missions/{test_user}")
        assert len(get_res3.json()["completed"]) == 1
        assert len(get_res3.json()["active"]) == 0
        
        # Verify users eco points updated (50 + 100 reward = 150)
        async with aiosqlite.connect(setup_db) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT eco_points FROM users WHERE id = ?", (test_user,)) as cursor:
                row = await cursor.fetchone()
            assert row["eco_points"] == 150
