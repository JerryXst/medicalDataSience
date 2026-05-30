from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.import_tasks import router as import_tasks_router
from app.api.users import router as users_router
from app.core.request_context import RequestContextMiddleware
from app.core.settings import settings


app = FastAPI(
    title="Medical Data Science API",
    version="0.1.0",
    description="API for pharmaceutical flow data ingestion and normalization.",
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(import_tasks_router, prefix="/api")
app.include_router(audit_logs_router, prefix="/api")
app.include_router(users_router, prefix="/api")
