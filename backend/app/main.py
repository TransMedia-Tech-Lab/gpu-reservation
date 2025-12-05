from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routes import router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    summary="研究室GPUの稼働状況と予約管理用バックエンド",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def health_check():
    return {"status": "ok", "message": "GPU Reservation Backend is running"}
