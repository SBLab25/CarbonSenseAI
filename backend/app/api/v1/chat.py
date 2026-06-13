import json
import aiosqlite
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, UserProfile
from app.db.database import get_db
from app.services import gemini_service
from app.middleware.rate_limiter import check_rate_limit

router = APIRouter(tags=["chat"])

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, db: aiosqlite.Connection = Depends(get_db)):
    # Check rate limit
    check_rate_limit(req.user_id, "chat", "rate_limit_chat_rpm")
    
    # Fetch user profile
    async with db.execute("SELECT * FROM users WHERE id = ?", (req.user_id,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
        
    profile = UserProfile(**dict(row))
    
    # Personalize coach system prompt
    system_prompt = f"""You are {profile.name}'s personal sustainability coach.
Tone: warm, expert, specific, encouraging, NOT preachy.
The user lives in {profile.city or 'unknown'}, {profile.country or 'unknown'}.
Their lifestyle is {profile.lifestyle_type or 'unknown'}.
Their diet is {profile.diet_type or 'unknown'}.
Their primary transport is {profile.primary_transport or 'unknown'}.
Their baseline monthly footprint is {profile.baseline_footprint_kg} kg CO2.
Their current Eco Points are {profile.eco_points}.

Keep your responses conversational, practical, and action-oriented. Reference their profile details to give highly personalized, practical advice. Limit your response to 150-200 words.
"""

    async def event_generator():
        try:
            async for token in gemini_service.stream_generate(
                system_prompt=system_prompt,
                user_message=req.message,
                history=req.history
            ):
                yield f"data: {token}\n\n"
            yield "data: [PIPELINE_COMPLETE]\n\n"
        except Exception:
            yield "data: [ERROR] Coaching temporarily unavailable.\n\n"
            yield "data: [PIPELINE_COMPLETE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )
