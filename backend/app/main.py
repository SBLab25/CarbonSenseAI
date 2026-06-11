from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.database import init_db

# Import routers
from app.api.v1.users import router as users_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.activities import router as activities_router
from app.api.v1.carbon import router as carbon_router
from app.api.v1.agents import router as agents_router
from app.api.v1.missions import router as missions_router
from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event: initialize database
    await init_db()
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title="CarbonSense AI",
        description="Multi-agent carbon footprint coaching platform",
        version="1.0.0",
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

    # Include all routers under prefix "/api/v1"
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(onboarding_router, prefix="/api/v1")
    app.include_router(activities_router, prefix="/api/v1")
    app.include_router(carbon_router, prefix="/api/v1")
    app.include_router(agents_router, prefix="/api/v1")
    app.include_router(missions_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(health_router, prefix="/api/v1")

    return app

app = create_app()
