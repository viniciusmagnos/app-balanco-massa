from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import analysis
from .services.file_service import cleanup_old_files


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_old_files(max_age_hours=24)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Balanço de Massa",
    description="Mass balance calculator for civil engineering earthwork analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
