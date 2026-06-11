import pytest
import datetime
import aiosqlite
from app.services.insights_cache import insights_cache
from app.config import settings

@pytest.mark.asyncio
async def test_cache_miss_returns_none(setup_db):
    user_id = "nonexistent-user"
    val = await insights_cache.get(user_id, "analyst")
    assert val is None

@pytest.mark.asyncio
async def test_cache_set_and_get(setup_db, test_user):
    user_id = test_user
    content = '{"key": "value"}'
    await insights_cache.set(user_id, "analyst", content)
    
    val = await insights_cache.get(user_id, "analyst")
    assert val == content

@pytest.mark.asyncio
async def test_cache_invalidation(setup_db, test_user):
    user_id = test_user
    content = '{"key": "to-be-invalidated"}'
    await insights_cache.set(user_id, "planner", content)
    
    # Verify it exists
    val = await insights_cache.get(user_id, "planner")
    assert val == content
    
    # Invalidate
    await insights_cache.invalidate(user_id)
    
    # Verify it is gone
    val = await insights_cache.get(user_id, "planner")
    assert val is None

@pytest.mark.asyncio
async def test_cache_ttl_expired(setup_db, test_user):
    user_id = test_user
    content = '{"key": "expired-data"}'
    
    # Manually insert an expired cache entry
    async with aiosqlite.connect(settings.database_url) as db:
        now = datetime.datetime.now()
        generated_at = (now - datetime.timedelta(hours=25)).strftime("%Y-%m-%d %H:%M:%S")
        valid_until = (now - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        await db.execute(
            """
            INSERT INTO insights_cache (user_id, agent_type, content_json, generated_at, valid_until, is_valid)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (user_id, "analyst_expired", content, generated_at, valid_until)
        )
        await db.commit()
        
    # Attempt to retrieve
    val = await insights_cache.get(user_id, "analyst_expired")
    assert val is None
