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

    from core.icon_assets import ensure_icons_extracted_from_db, fix_existing_icons

    db_stats = ensure_icons_extracted_from_db(ICONS_DIR)
    local_stats = fix_existing_icons(ICONS_DIR)
    total = sum(db_stats.values()) + sum(local_stats.values())
    if total:
        parts = []
        total_cropped = db_stats.get("cropped", 0) + local_stats.get("cropped", 0)
        total_new = db_stats.get("new", 0)
        total_needs_pil = db_stats.get("needs_pil", 0) + local_stats.get("needs_pil", 0)
        if total_cropped:
            parts.append(f"已裁剪 {total_cropped} 个 mipmap 条带")
        if total_new:
            parts.append(f"新增 {total_new} 个")
        if total_needs_pil:
            parts.append(f"{total_needs_pil} 个需 Pillow 裁剪")
        if parts:
            print(f"  图标: {', '.join(parts)}（共 {total} 个）")
        else:
            print(f"  图标: {total} 个文件已就绪")

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


ICONS_DIR = Path(__file__).resolve().parent / "data" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/v1/static/icons", StaticFiles(directory=str(ICONS_DIR)), name="icons")

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
