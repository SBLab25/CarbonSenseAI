import pytest
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_get_user_profile(setup_db, test_user):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/users/{test_user}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user
        assert data["name"] == "Test User"

@pytest.mark.asyncio
async def test_get_user_not_found(setup_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/users/nonexistent-user-uuid")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_user_profile(setup_db, test_user):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Updated Name",
            "country": "India",
            "city": "Bangalore",
            "lifestyle_type": "urban",
            "diet_type": "vegan",
            "primary_transport": "bicycle",
            "weekly_transport_km": 10.0,
            "monthly_electricity_kwh": 50.0,
            "heating_type": "none",
            "monthly_target_reduction_pct": 20.0
        }
        response = await client.put(f"/api/v1/users/{test_user}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["diet_type"] == "vegan"
        assert data["primary_transport"] == "bicycle"
        assert data["monthly_target_reduction_pct"] == 20.0
