"""布局 API 入口（v2 流水线）。"""

from __future__ import annotations

from models.schemas import LayoutComputeRequest, LayoutComputeResponse
from core.layout_pipeline import run_layout_pipeline


def _resolve_layout_context():
    from core.game_session import SESSION
    from db.environment_store import list_environments
    from db.recipe_loader_db import load_recipe_database

    if SESSION.env_key and SESSION.active_save_key and SESSION.progress_loaded:
        return load_recipe_database(SESSION.env_key, save_key=SESSION.active_save_key)

    envs = list_environments()
    if envs:
        ek = envs[0]["env_key"]
        return load_recipe_database(ek, save_key=None)

    from core.recipe_loader import load_database

    return load_database()


def compute_layout(request: LayoutComputeRequest) -> LayoutComputeResponse:
    db = _resolve_layout_context()
    return run_layout_pipeline(request, db)
