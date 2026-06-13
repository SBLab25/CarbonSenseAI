import pytest
import httpx
from app.main import app
from app.services.insights_cache import insights_cache

@pytest.mark.asyncio
async def test_get_insights_empty(setup_db, test_user):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/agents/insights/{test_user}")
        assert response.status_code == 200
        data = response.json()
        assert data["analyst"] is None
        assert data["planner"] is None

@pytest.mark.asyncio
async def test_get_insights_with_data(setup_db, test_user):
    # Set cache values
    analyst_json = '{"primary_hotspot": "energy", "hotspots": [], "behavioral_patterns": [], "quick_win_available": true, "analysis_confidence": "high"}'
    planner_json = '{"strategies": [], "total_potential_saving_kg": 0.0, "recommended_goal_pct": 15.0, "thirty_day_focus": "Energy"}'
    await insights_cache.set(test_user, "analyst", analyst_json)
    await insights_cache.set(test_user, "planner", planner_json)
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/agents/insights/{test_user}")
        assert response.status_code == 200
        data = response.json()
        assert data["analyst"]["primary_hotspot"] == "energy"
        assert data["planner"]["recommended_goal_pct"] == 15.0

@pytest.mark.asyncio
async def test_analyze_endpoint(setup_db, test_user, mock_gemini):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"user_id": test_user}
        response = await client.post("/api/v1/agents/analyze", json=payload)
        assert response.status_code == 200
        
        # Verify it returns an event stream
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        body = response.text
        assert "data: Test" in body
        assert "data: [PIPELINE_COMPLETE]" in body

@pytest.mark.asyncio
async def test_chat_stream_endpoint(setup_db, test_user, mock_gemini):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "user_id": test_user,
            "message": "Hello Coach",
            "history": []
        }
        response = await client.post("/api/v1/chat/stream", json=payload)
        assert response.status_code == 200
        
        # Verify it returns an event stream
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        body = response.text
        assert "data: Test" in body
        assert "data: [PIPELINE_COMPLETE]" in body
        
@pytest.mark.asyncio
async def test_health_endpoint(setup_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "CarbonSense AI"}
