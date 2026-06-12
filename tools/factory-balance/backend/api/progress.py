from __future__ import annotations

from fastapi import APIRouter, Query

from pathlib import Path

from core.factorio_paths import load_paths, read_last_played_save_name
from core.game_session import SESSION
from core.save_index import list_saves
from core.session_coordinator import (
    build_catalog_response,
    import_save_progress,
    purge_cache_response,
)
from db.environment_store import has_any_environment, list_environments
from db.save_store import active_progress_stale, get_save_progress_state
from models.schemas import (
    FactorioStatusResponse,
    ItemCatalogResponse,
    LoadProgressRequest,
    ProgressResponse,
    PurgeCacheResponse,
    SaveInfoModel,
)

router = APIRouter(tags=["progress"])


@router.get("/items/catalog", response_model=ItemCatalogResponse)
def items_catalog(
    mode: str = Query("progress", description="progress=仅当前存档进度, full=完整全配方"),
) -> ItemCatalogResponse:
    scope = "save" if mode != "full" else "environment"
    return build_catalog_response(scope)


@router.get("/factorio/status", response_model=FactorioStatusResponse)
def factorio_status() -> FactorioStatusResponse:
    paths = load_paths()
    saves = list_saves()
    envs = list_environments()
    return FactorioStatusResponse(
        user_data_dir=str(paths.user_data),
        saves_dir=str(paths.saves_dir),
        executable=str(paths.executable) if paths.executable else None,
        executable_source=paths.executable_source,
        save_count=len(saves),
        last_played_save=read_last_played_save_name(paths.user_data),
        session_updated_at=SESSION.updated_at,
        database_source=SESSION.database_source,
        progress_loaded=SESSION.progress_loaded,
        progress_stale=active_progress_stale(SESSION.active_save_key),
        active_save_key=SESSION.active_save_key,
        enabled_recipe_count=len(SESSION.enabled_recipes),
        craftable_item_count=len(SESSION.craftable_items),
        has_recipe_pack=has_any_environment(),
        pack_count=len(envs),
    )


@router.get("/factorio/saves", response_model=list[SaveInfoModel])
def factorio_saves() -> list[SaveInfoModel]:
    return [
        SaveInfoModel(
            name=s.name,
            path=s.path,
            modified_at=s.modified_at,
            is_last_played=s.is_last_played,
            game_version=s.game_version,
            **get_save_progress_state(s.name, Path(s.path)),
        )
        for s in list_saves()
    ]


@router.post("/factorio/load-progress", response_model=ProgressResponse)
def load_progress(body: LoadProgressRequest) -> ProgressResponse:
    result = import_save_progress(body.save, reexport=body.reexport)
    return result.response


@router.post("/factorio/refresh-prototypes")
def refresh_prototypes() -> dict:
    warnings = SESSION.refresh_snapshot()
    return {
        "ok": has_any_environment(),
        "database_source": SESSION.database_source,
        "warnings": warnings,
        "pack_count": len(list_environments()),
    }


@router.post("/factorio/purge-cache", response_model=PurgeCacheResponse)
def purge_cache(keep_active: bool = Query(True)) -> PurgeCacheResponse:
    return purge_cache_response(keep_active=keep_active)
