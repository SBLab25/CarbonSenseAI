import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.schemas import AnalyzeRequest
from app.services.agent_orchestrator import orchestrator
from app.services.insights_cache import insights_cache
from app.middleware.rate_limiter import check_rate_limit

router = APIRouter(tags=["agents"])

@router.post("/agents/analyze")
async def analyze_footprint(req: AnalyzeRequest):
    # Check rate limit (analyze endpoint, 3/hour)
    check_rate_limit(req.user_id, "analyze", "rate_limit_analyze_rph")
    
    async def event_generator():
        try:
            async for token in orchestrator.run_pipeline(req.user_id):
                # SSE data framing
                safe_token = token.replace("\n", "\\n")
                yield f"data: {safe_token}\n\n"
            yield "data: [PIPELINE_COMPLETE]\n\n"
        except Exception:
            yield "data: [ERROR] Analysis temporarily unavailable.\n\n"
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

@router.get("/agents/insights/{user_id}")
async def get_insights(user_id: str):
    analyst_json = await insights_cache.get(user_id, "analyst")
    planner_json = await insights_cache.get(user_id, "planner")
    
    return {
        "analyst": json.loads(analyst_json) if analyst_json else None,
        "planner": json.loads(planner_json) if planner_json else None
    }
