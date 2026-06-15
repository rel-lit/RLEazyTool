"""存档进度导入、缓存清理等跨层编排。"""

from __future__ import annotations

from dataclasses import dataclass

from core.game_session import SESSION
from core.progress_export import export_progress_from_save
from db.app_state import purge_stale
from db.environment_store import has_any_environment, list_environments
from db.save_store import get_enabled_recipe_names, get_save_binding, active_progress_stale, is_save_progress_stale, get_game_save_path
from models.schemas import ItemCatalogResponse, ItemInfo, ProgressResponse, PurgeCacheResponse


def _item_info(i) -> ItemInfo:
    return ItemInfo(
        name=i.name,
        label=i.label,
        group=i.group,
        is_raw=i.is_raw,
        expansion=i.expansion,
        icon_slug=getattr(i, "icon_slug", None),
    )


def build_catalog_response(scope: str = "save") -> ItemCatalogResponse:
    catalog = SESSION.get_item_catalog(scope)
    envs = list_environments()
    stale = scope == "save" and active_progress_stale(SESSION.active_save_key)
    return ItemCatalogResponse(
        all_items=[_item_info(i) for i in catalog.all_items],
        manufacture_items=[_item_info(i) for i in catalog.manufacture_items],
        supply_items=[_item_info(i) for i in catalog.supply_items],
        database_source=SESSION.database_source,
        progress_loaded=SESSION.progress_loaded,
        progress_stale=stale,
        active_save_key=SESSION.active_save_key,
        catalog_mode="progress" if scope == "save" else "full",
        has_recipe_pack=has_any_environment(),
        pack_count=len(envs),
    )


@dataclass
class ImportProgressResult:
    ok: bool
    save_key: str | None
    warnings: list[str]
    response: ProgressResponse


def import_save_progress(save: str, *, reexport: bool) -> ImportProgressResult:
    """导入存档进度：环境检测 → 导出 → gate 写入 → 会话绑定 → catalog 响应。"""
    warnings: list[str] = []
    save_key, export_warnings = export_progress_from_save(save, reexport=reexport)
    warnings.extend(export_warnings)

    if save_key is None:
        return ImportProgressResult(
            ok=False,
            save_key=None,
            warnings=warnings,
            response=ProgressResponse(
                ok=False,
                warnings=warnings,
                database_source=SESSION.database_source,
            ),
        )

    SESSION.bind_save(save_key, warnings)
    enabled = get_enabled_recipe_names(save_key)
    catalog = build_catalog_response("save")
    save_path = get_game_save_path(save_key)
    progress_stale = (
        is_save_progress_stale(save_key, save_path) if save_path is not None else False
    )
    return ImportProgressResult(
        ok=True,
        save_key=save_key,
        warnings=list(SESSION.warnings),
        response=ProgressResponse(
            ok=True,
            save=save_key,
            researched_technology_count=0,
            enabled_recipe_count=len(enabled),
            craftable_items=catalog.manufacture_items,
            manufacture_items=catalog.manufacture_items,
            supply_items=catalog.supply_items,
            warnings=SESSION.warnings,
            database_source=SESSION.database_source,
            progress_stale=progress_stale,
            reexported=reexport,
        ),
    )


@dataclass
class PurgeCacheResult:
    deleted_packs: int
    deleted_progress: int
    legacy_files_removed: list[str]
    progress_still_loaded: bool


def purge_application_cache(*, keep_active: bool) -> PurgeCacheResult:
    """清理 SQLite 缓存并同步 SESSION 内存态。"""
    result = purge_stale(keep_active=keep_active)
    if keep_active:
        restored = SESSION.restore()
    else:
        SESSION.reset()
        restored = False

    return PurgeCacheResult(
        deleted_packs=result["deleted_environments"],
        deleted_progress=result["deleted_saves"],
        legacy_files_removed=result["legacy_files_removed"],
        progress_still_loaded=restored,
    )


def purge_cache_response(*, keep_active: bool) -> PurgeCacheResponse:
    r = purge_application_cache(keep_active=keep_active)
    return PurgeCacheResponse(
        ok=True,
        deleted_packs=r.deleted_packs,
        deleted_progress=r.deleted_progress,
        legacy_files_removed=r.legacy_files_removed,
    )
