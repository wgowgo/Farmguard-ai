from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import fields, admin, knowledge, crops, disasters
from app.config import settings
from app.services.crop_registry import list_crops


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="팜가드 AI API",
    description="필지 단위 병해충, 기상 리스크 예측 및 행동 권고 서비스",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fields.router)
app.include_router(admin.router)
app.include_router(admin.router_alerts)
app.include_router(knowledge.router)
app.include_router(crops.router)
app.include_router(disasters.router)


@app.get("/")
async def root():
    return {
        "service": "팜가드 AI",
        "version": "1.0.0",
        "demo_mode": settings.demo_mode,
        "supported_crops": len(list_crops()),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
