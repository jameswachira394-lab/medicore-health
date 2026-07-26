from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared_common.database import Base
from shared_common.logging_config import configure_logging

from app.core.config import settings
from app.core.db import engine
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)
    # In production, schema management is done via Alembic migrations run
    # in the CI/CD pipeline, not create_all(). Kept here for local/dev speed.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="MediCore Authentication Service",
    version="1.0.0",
    description="Handles registration, login, MFA, JWT issuance, and password resets.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}


@app.get("/ready", tags=["ops"])
def ready():
    return {"status": "ready"}
