from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import projects, findings, stats, ingest
from app.routers import scans, dependencies


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_title, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(findings.router)
app.include_router(scans.router)
app.include_router(dependencies.router)
app.include_router(stats.router)
app.include_router(ingest.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
