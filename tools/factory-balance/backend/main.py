"""FastAPI 入口。"""

from __future__ import annotations

from pathlib import Path

from contextlib import asynccontextmanager

from console_encoding import configure_console_utf8

configure_console_utf8()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.layout import router as layout_router
from api.progress import router as progress_router
from api.recipes import router as recipes_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    from db.connection import init_db
    from core.game_session import SESSION

    init_db(reset=False)
    SESSION.restore()
    yield


app = FastAPI(title="异星自平衡布局", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipes_router, prefix="/api/v1")
app.include_router(progress_router, prefix="/api/v1")
app.include_router(layout_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
