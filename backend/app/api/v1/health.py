"""Health check endpoint — used as the Render free-tier keepalive target."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Return service liveness status.

    This endpoint is called every 14 minutes by the React frontend to
    prevent Render's free-tier service from spinning down due to inactivity.
    """
    return {"status": "ok", "service": "CarbonSense AI"}
