import pytest
import httpx
from app.main import app
from app.services.insights_cache import insights_cache

@pytest.mark.asyncio
async def test_log_structured_activity(setup_db, test_user):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "user_id": test_user,
            "category": "transport",
            "type": "car_petrol",
            "amount": 20.0,
            "unit": "km",
            "notes": "Driving to work"
        }
        response = await client.post("/api/v1/activities", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "transport"
        assert data["co2_kg"] == pytest.approx(4.2, rel=0.01)

@pytest.mark.asyncio
async def test_log_nl_activity(setup_db, test_user, mock_gemini):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "user_id": test_user,
            "description": "I drove 20km to work"
        }
        response = await client.post("/api/v1/activities/parse-nl", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["co2_kg"] == pytest.approx(4.2, rel=0.01)
        assert data["parsed"]["category"] == "transport"

@pytest.mark.asyncio
async def test_get_activity_history(setup_db, test_user):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Clear existing activities
        import aiosqlite
        async with aiosqlite.connect(setup_db) as db:
            await db.execute("DELETE FROM activities WHERE user_id = ?", (test_user,))
            await db.commit()

        # Log 3 activities
        for i in range(3):
            payload = {
                "user_id": test_user,
                "category": "transport",
                "type": "train",
                "amount": 10.0 * (i + 1),
                "unit": "km"
            }
            await client.post("/api/v1/activities", json=payload)
            
        response = await client.get(f"/api/v1/activities/{test_user}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 3
        assert data["total"] == 3

@pytest.mark.asyncio
async def test_delete_activity(setup_db, test_user):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Clear existing activities
        import aiosqlite
        async with aiosqlite.connect(setup_db) as db:
            await db.execute("DELETE FROM activities WHERE user_id = ?", (test_user,))
            await db.commit()

        # Log 1 activity
        payload = {
            "user_id": test_user,
            "category": "food",
            "type": "beef",
            "amount": 1.0,
            "unit": "kg"
        }
        res = await client.post("/api/v1/activities", json=payload)
        activity_id = res.json()["activity_id"]
        
        # Verify it is in history
        history_res = await client.get(f"/api/v1/activities/{test_user}")
        assert len(history_res.json()["activities"]) == 1
        
        # Delete it
        del_res = await client.post(f"/api/v1/activities" + f"/{activity_id}" if hasattr(client, "delete") else f"/api/v1/activities/{activity_id}")
        # Wait, the delete endpoint method is DELETE, let's use client.delete
        del_res = await client.delete(f"/api/v1/activities/{activity_id}")
        assert del_res.status_code == 200
        
        # Verify history is empty
        history_res2 = await client.get(f"/api/v1/activities/{test_user}")
        assert len(history_res2.json()["activities"]) == 0

@pytest.mark.asyncio
async def test_activity_invalidates_cache(setup_db, test_user):
    # Set dummy cache
    await insights_cache.set(test_user, "analyst", '{"insights": "valid"}')
    
    # Verify cached value exists
    val = await insights_cache.get(test_user, "analyst")
    assert val is not None
    
    # Log an activity via API
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "user_id": test_user,
            "category": "shopping",
            "type": "clothing",
            "amount": 2.0,
            "unit": "item"
        }
        await client.post("/api/v1/activities", json=payload)
        
    # Verify cache is invalidated
    val_after = await insights_cache.get(test_user, "analyst")
    assert val_after is None
