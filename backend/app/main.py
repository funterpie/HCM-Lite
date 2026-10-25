from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.modules.ai.router import router as ai_router
from app.modules.attendance.router import router as attendance_router
from app.modules.auth.router import router as auth_router
from app.modules.comms.router import router as comms_router
from app.modules.dashboards.router import router as dashboards_router
from app.modules.employees.router import router as employees_router
from app.modules.leave.router import router as leave_router
from app.modules.payroll.router import router as payroll_router
from app.modules.settings.router import router as settings_router
from app.modules.users.router import router as users_router
from app.modules.auth.service import ensure_configured_admin

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ensure_configured_admin()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)
api_router = APIRouter()


@api_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


for module_router in (
    auth_router,
    settings_router,
    employees_router,
    attendance_router,
    leave_router,
    payroll_router,
    dashboards_router,
    ai_router,
    users_router,
    comms_router,
):
    api_router.include_router(module_router)

app.include_router(api_router)
app.include_router(api_router, prefix="/api")
