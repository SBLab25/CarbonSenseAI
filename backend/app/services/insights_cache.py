import datetime
from typing import Optional, Any
from app.db.database import get_db_context

class InsightsCache:
    async def get(self, user_id: str, agent_type: str, db: Optional[Any] = None) -> str | None:
        if db is not None:
            return await self._get_with_conn(db, user_id, agent_type)
        async with get_db_context() as conn:
            return await self._get_with_conn(conn, user_id, agent_type)

    async def _get_with_conn(self, db: Any, user_id: str, agent_type: str) -> str | None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        async with db.execute(
            "SELECT content_json FROM insights_cache WHERE user_id = ? AND agent_type = ? AND is_valid = 1 AND valid_until > ?",
            (user_id, agent_type, now)
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            if isinstance(row, dict):
                return row["content_json"]
            try:
                return row["content_json"]
            except (TypeError, IndexError):
                return row[0] if isinstance(row, tuple) else None
        return None

    async def set(self, user_id: str, agent_type: str, content_json: str, db: Optional[Any] = None):
        if db is not None:
            await self._set_with_conn(db, user_id, agent_type, content_json)
        else:
            async with get_db_context() as conn:
                await self._set_with_conn(conn, user_id, agent_type, content_json)
                await conn.commit()

    async def _set_with_conn(self, db: Any, user_id: str, agent_type: str, content_json: str):
        now = datetime.datetime.now()
        valid_until = (now + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        await db.execute(
            "INSERT INTO insights_cache (user_id, agent_type, content_json, generated_at, valid_until, is_valid) VALUES (?, ?, ?, ?, ?, 1)",
            (user_id, agent_type, content_json, now_str, valid_until)
        )

    async def invalidate(self, user_id: str, db: Optional[Any] = None):
        if db is not None:
            await self._invalidate_with_conn(db, user_id)
        else:
            async with get_db_context() as conn:
                await self._invalidate_with_conn(conn, user_id)
                await conn.commit()

    async def _invalidate_with_conn(self, db: Any, user_id: str):
        await db.execute(
            "UPDATE insights_cache SET is_valid = 0 WHERE user_id = ?",
            (user_id,)
        )

insights_cache = InsightsCache()
