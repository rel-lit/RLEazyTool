"""FastAPI 入口。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from console_encoding import configure_console_utf8

configure_console_utf8()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.layout import router as layout_router
from api.progress import router as progress_router
from api.recipes import router as recipes_router
from core.icon_store import ICONS_DIR, count_icons, count_mipmap_strips, ensure_icons_dir


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from db.connection import init_db
    from core.game_session import SESSION

    init_db(reset=False)
    SESSION.restore()

    ensure_icons_dir()
    icon_count = count_icons()
    strip_count = count_mipmap_strips()
    if strip_count:
        print(f"  图标: {icon_count} 个文件，其中 {strip_count} 个仍是 mipmap 条带。请运行 scripts/prepare_icons.py 修复。")
    elif icon_count:
        print(f"  图标: {icon_count} 个文件已就绪")

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


# 注意：mount 顺序决定匹配优先级。
# /api/v1/static/icons 必须在前端 catch-all "/" 之前注册，
# 否则前端 SPA 会把图标请求当作路由并返回 index.html/404。
ensure_icons_dir()
app.mount("/api/v1/static/icons", StaticFiles(directory=str(ICONS_DIR)), name="icons")

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
