from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ROUTE_MAP, settings
from app.routers import proxy

app = FastAPI(
    title="MediCore API Gateway",
    version="1.0.0",
    description="Single entry point for the MediCore frontend; routes requests to the appropriate backend microservice.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME, "routes": list(ROUTE_MAP.keys())}


app.include_router(proxy.router)
