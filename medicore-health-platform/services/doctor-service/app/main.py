from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared_common.database import Base
from shared_common.logging_config import configure_logging

from app.core.config import settings
from app.core.db import engine
from app.routers import doctors


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="MediCore Doctor Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(doctors.router)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}
