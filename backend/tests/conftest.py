import pytest
import asyncio
import os
import tempfile
from typing import AsyncGenerator
from app.db.database import init_db
from app.services import gemini_service
import aiosqlite

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test_carbonsense.db"
    return str(db_file)

@pytest.fixture(scope="session")
async def setup_db(test_db_path):
    # Set environment variable DATABASE_URL to test database path
    os.environ["DATABASE_URL"] = test_db_path
    
    # Dynamically assign database_url in settings object
    from app.config import settings
    settings.database_url = test_db_path
    
    # Initialize the database schema
    await init_db()
    yield test_db_path
    
    # Cleanup env
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]

@pytest.fixture(scope="function")
async def test_user(setup_db) -> str:
    import uuid
    user_id = str(uuid.uuid4())
    async with aiosqlite.connect(setup_db) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """
            INSERT INTO users (
                id, name, country, city, lifestyle_type, diet_type, 
                primary_transport, weekly_transport_km, monthly_electricity_kwh, 
                heating_type, baseline_footprint_kg, monthly_target_reduction_pct, eco_points
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, "Test User", "India", "Bangalore", "urban", "vegetarian",
                "car_petrol", 50.0, 100.0, "electricity", 200.0, 15.0, 50
            )
        )
        await db.commit()
    
    return user_id

@pytest.fixture(scope="function")
def mock_gemini(monkeypatch):
    # Mock parse_activity_nl
    async def mock_parse(description: str):
        return {
            "category": "transport",
            "type": "car_petrol",
            "amount": 20.0,
            "unit": "km",
            "confidence": "high"
        }
    
    # Mock function_call
    async def mock_func_call(system_prompt: str, user_message: str, function_schema: dict) -> dict:
        schema_name = function_schema.get("name")
        if schema_name == "set_baseline_footprint":
            return {
                "monthly_total_kg": 180.0,
                "transport_kg": 50.0,
                "energy_kg": 70.0,
                "food_kg": 40.0,
                "shopping_kg": 20.0,
                "primary_hotspot": "energy",
                "confidence": "high"
            }
        elif schema_name == "analyze_carbon_footprint":
            return {
                "primary_hotspot": "transport",
                "hotspots": [
                    {
                        "category": "transport",
                        "pct_of_total": 45.0,
                        "vs_baseline_change_pct": 10.0,
                        "key_behaviors": ["Frequent solo driving"],
                        "reduction_opportunity_kg": 25.0
                    }
                ],
                "behavioral_patterns": ["Commuting alone daily"],
                "quick_win_available": True,
                "analysis_confidence": "high"
            }
        elif schema_name == "create_reduction_plan":
            return {
                "strategies": [
                    {
                        "title": "Carpool to work",
                        "action": "Coordinate carpooling with coworkers twice a week",
                        "category": "transport",
                        "monthly_saving_kg": 30.0,
                        "difficulty": "easy",
                        "timeframe_days": 7,
                        "mission_type": "carpool"
                    }
                ],
                "total_potential_saving_kg": 30.0,
                "recommended_goal_pct": 15.0,
                "thirty_day_focus": "Carpooling and transport optimization"
            }
        return {}

    # Mock stream_generate
    async def mock_stream(system_prompt, user_message, history=None):
        for token in ["Test", " coaching", " response", " from", " Gemini."]:
            yield token

    monkeypatch.setattr(gemini_service, "parse_activity_nl", mock_parse)
    monkeypatch.setattr(gemini_service, "function_call", mock_func_call)
    monkeypatch.setattr(gemini_service, "stream_generate", mock_stream)
