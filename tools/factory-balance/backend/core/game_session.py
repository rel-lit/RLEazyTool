"""会话：仅通过终态 SQLite 读写。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.item_catalog import ItemCatalog
from db.app_state import get_active_save_key, get_catalog_scope, set_active_save_key, set_catalog_scope
from db.catalog_query import ensure_build_exists, query_catalog
from db.environment_store import list_environments
from db.recipe_loader_db import load_recipe_database
from db.save_store import get_enabled_recipe_names, get_save_binding


@dataclass
class GameSession:
    active_save_key: str | None = None
    catalog_scope: str = "save"
    warnings: list[str] = field(default_factory=list)
    updated_at: str | None = None

    def restore(self) -> bool:
        self.active_save_key = get_active_save_key()
        self.catalog_scope = get_catalog_scope()
        return self.active_save_key is not None

    @property
    def progress_loaded(self) -> bool:
        return self.active_save_key is not None and get_save_binding(self.active_save_key) is not None

    @property
    def env_key(self) -> str | None:
        if not self.active_save_key:
            return None
        binding = get_save_binding(self.active_save_key)
        return binding["env_key"] if binding else None

    @property
    def enabled_recipes(self) -> set[str]:
        if not self.active_save_key:
            return set()
        return set(get_enabled_recipe_names(self.active_save_key))

    @property
    def craftable_items(self) -> set[str]:
        cat = self.get_item_catalog("save")
        return {i.name for i in cat.manufacture_items}

    @property
    def database_source(self) -> str:
        if not self.env_key:
            return "sqlite-empty"
        return f"env:{self.env_key}"

    def bind_save(self, save_key: str, warnings: list[str] | None = None) -> None:
        self.active_save_key = save_key
        set_active_save_key(save_key)
        self.catalog_scope = "save"
        set_catalog_scope("save")
        self.warnings = list(warnings or [])
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def refresh_snapshot(self) -> list[str]:
        from db.ingest import ingest_snapshot_from_dump

        _, warnings = ingest_snapshot_from_dump()
        return warnings

    def get_active_database(self):
        from core.recipe_loader import RecipeDatabase

        if not self.env_key:
            return RecipeDatabase(items={}, recipes={}, recipes_by_product={})
        return load_recipe_database(self.env_key, save_key=self.active_save_key)

    def get_item_catalog(self, scope: str | None = None) -> ItemCatalog:
        empty = ItemCatalog(all_items=[], manufacture_items=[], supply_items=[])
        scope = scope or self.catalog_scope

        if scope == "environment":
            ek = self.env_key
            if not ek:
                envs = list_environments()
                if not envs:
                    return empty
                ek = envs[0]["env_key"]
            ensure_build_exists("environment", ek, ek)
            return query_catalog(scope_kind="environment", scope_key=ek)

        if not self.active_save_key:
            return empty
        binding = get_save_binding(self.active_save_key)
        if not binding:
            return empty
        ek = binding["env_key"]
        ensure_build_exists("save", self.active_save_key, ek)
        return query_catalog(scope_kind="save", scope_key=self.active_save_key)

    def set_catalog_scope(self, scope: str) -> None:
        self.catalog_scope = scope
        set_catalog_scope(scope)

    def reset(self) -> None:
        self.active_save_key = None
        set_active_save_key(None)
        self.warnings = []
        self.updated_at = None


SESSION = GameSession()
