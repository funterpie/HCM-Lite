from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.errors import register_exception_handlers

# Routers
from app.modules.ai.router import router as ai_router
from app.modules.users.router import router as users_router
from app.modules.dashboards.router import router as dashboards_router

app = FastAPI(title="HCM Lite API", version="1.0.0")

# CORS setup
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Include routers under /api prefix per PROJECT.md
app.include_router(ai_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(dashboards_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/health")
async def api_health_check():
    return {"status": "ok"}
