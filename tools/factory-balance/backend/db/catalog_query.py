"""从 catalog_tag 查询 UI 列表。"""

from __future__ import annotations

import json

from core.icon_store import icon_slug_from_path
from core.item_catalog import ItemCatalog
from core.recipe_loader import ItemDef
from db.connection import get_connection


def _derive_icon_slug(icon_path: str | None) -> str | None:
    if not icon_path:
        return None
    try:
        return icon_slug_from_path(icon_path)
    except (ValueError, IndexError):
        return None


def _rows_for_panel(
    conn,
    scope_kind: str,
    scope_key: str,
    panel_code: str,
    locale: str,
) -> list[ItemDef]:
    panel = conn.execute(
        "SELECT require_tag, exclude_tags FROM ui_panel WHERE code = ?", (panel_code,)
    ).fetchone()
    if not panel:
        return []

    build = conn.execute(
        "SELECT id FROM catalog_build WHERE scope_kind = ? AND scope_key = ?",
        (scope_kind, scope_key),
    ).fetchone()
    if not build:
        return []

    build_id = int(build["id"])
    require_tag = panel["require_tag"]
    exclude = set(json.loads(panel["exclude_tags"] or "[]"))

    rows = conn.execute(
        """
        SELECT sr.name, sr.is_raw, sr.expansion, sr.item_subgroup, sr.icon,
               srt.label,
               GROUP_CONCAT(ct.tag_code) AS tags
        FROM catalog_tag ct
        JOIN snap_resource sr ON sr.id = ct.resource_id
        LEFT JOIN snap_resource_text srt ON srt.resource_id = sr.id AND srt.locale = ?
        WHERE ct.build_id = ? AND ct.tag_code = ?
        GROUP BY sr.id
        ORDER BY srt.label, sr.name
        """,
        (locale, build_id, require_tag),
    ).fetchall()

    out: list[ItemDef] = []
    for r in rows:
        tag_set = set((r["tags"] or "").split(",")) if r["tags"] else {require_tag}
        if tag_set & exclude:
            continue
        icon_path = r["icon"]
        icon_slug = _derive_icon_slug(icon_path) if icon_path else None
        out.append(
            ItemDef(
                name=r["name"],
                label=r["label"] or r["name"],
                is_raw=bool(r["is_raw"]),
                expansion=r["expansion"] or "base",
                group=r["item_subgroup"],
                icon_slug=icon_slug,
            )
        )
    return out


def query_catalog(
    *,
    scope_kind: str,
    scope_key: str,
    locale: str = "zh-CN",
) -> ItemCatalog:
    conn = get_connection()
    try:
        manufacture = _rows_for_panel(conn, scope_kind, scope_key, "manufacture", locale)
        supply = _rows_for_panel(conn, scope_kind, scope_key, "supply", locale)
        # D：统一数据源；manufacture / supply 是 D 的两个 tag 视图
        seen = {i.name for i in manufacture}
        all_items = manufacture + [i for i in supply if i.name not in seen]
        return ItemCatalog(all_items=all_items, manufacture_items=manufacture, supply_items=supply)
    finally:
        conn.close()


def ensure_build_exists(scope_kind: str, scope_key: str, env_key: str) -> None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM catalog_build WHERE scope_kind = ? AND scope_key = ?",
            (scope_kind, scope_key),
        ).fetchone()
        if row:
            return
    finally:
        conn.close()
    from db.catalog_builder import build_catalog

    build_catalog(scope_kind=scope_kind, scope_key=scope_key, env_key=env_key)
