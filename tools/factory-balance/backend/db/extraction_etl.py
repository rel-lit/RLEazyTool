"""从 dump 实体层解析地图抽取关系，并写入合成抽取配方。"""

from __future__ import annotations

import json
from typing import Any

EXTRACT_RECIPE_PREFIX = "extract:"
OFFSHORE_PUMP_ENTITY = "offshore-pump"
OFFSHORE_PUMP_FLUID = "water"


def ingest_world_extraction(
    conn,
    snapshot_id: int,
    raw: dict[str, Any],
    *,
    locale: str,
    resource_id_by_key: dict[tuple[str, str], int],
) -> None:
    """解析 resource / mining-drill / offshore-pump，写入抽取表与合成配方。"""
    conn.execute("DELETE FROM snap_resource_extraction WHERE snapshot_id = ?", (snapshot_id,))
    _delete_synthetic_extract_recipes(conn, snapshot_id)

    rows: list[tuple[str, str, str, str | None, str | None, str | None]] = []

    for name, proto in (raw.get("resource") or {}).items():
        if not isinstance(proto, dict):
            continue
        category = proto.get("category")
        infinite = 1 if proto.get("infinite") else 0
        conn.execute(
            """
            INSERT INTO snap_map_resource (snapshot_id, name, category, infinite)
            VALUES (?, ?, ?, ?)
            """,
            (snapshot_id, name, str(category) if category else None, infinite),
        )
        # basic-fluid 资源（如原油）用 fluid_well / pumpjack；固体资源用 map_resource / mining-drill
        source_type = "fluid_well" if category == "basic-fluid" else "map_resource"
        minable = proto.get("minable") or {}
        result = minable.get("result")
        if result:
            kind = "fluid" if category == "basic-fluid" else "item"
            rows.append((source_type, name, kind, str(result), None, category))
        for entry in minable.get("results") or []:
            if not isinstance(entry, dict) or not entry.get("name"):
                continue
            kind = str(entry.get("type") or "item")
            rows.append((source_type, name, kind, str(entry["name"]), None, category))

    for table in ("mining-drill",):
        for entity_name, proto in (raw.get(table) or {}).items():
            if not isinstance(proto, dict):
                continue
            categories = proto.get("resource_categories") or []
            if isinstance(categories, dict):
                categories = list(categories.keys())
            conn.execute(
                """
                INSERT INTO snap_extractor (snapshot_id, entity_name, entity_type, resource_categories)
                VALUES (?, ?, ?, ?)
                """,
                (snapshot_id, entity_name, table, json.dumps(list(categories), ensure_ascii=False)),
            )

    for entity_name, proto in (raw.get("offshore-pump") or {}).items():
        if not isinstance(proto, dict):
            continue
        conn.execute(
            """
            INSERT INTO snap_extractor
            (snapshot_id, entity_name, entity_type, resource_categories, output_kind, output_name)
            VALUES (?, ?, 'offshore-pump', NULL, 'fluid', ?)
            """,
            (snapshot_id, entity_name, OFFSHORE_PUMP_FLUID),
        )
        rows.append(
            ("offshore_pump", entity_name, "fluid", OFFSHORE_PUMP_FLUID, OFFSHORE_PUMP_ENTITY, None)
        )

    category_to_extractor = _default_extractors(conn, snapshot_id)
    deduped: set[tuple[str, str, str, str | None, str | None]] = set()
    for source_type, source_name, kind, resource_name, extractor, category in rows:
        key = (kind, resource_name, source_type, source_name)
        if key in deduped:
            continue
        deduped.add(key)
        if extractor is None and category:
            extractor = category_to_extractor.get(str(category))
        conn.execute(
            """
            INSERT INTO snap_resource_extraction
            (snapshot_id, resource_kind, resource_name, source_type, source_name,
             extractor_entity, resource_category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                kind,
                resource_name,
                source_type,
                source_name,
                extractor,
                str(category) if category else None,
            ),
        )

    _insert_synthetic_extract_recipes(
        conn,
        snapshot_id,
        locale,
        resource_id_by_key,
        raw,
    )


def _default_extractors(conn, snapshot_id: int) -> dict[str, str]:
    """每种 resource_category 选一个代表抽取建筑（优先常见名）。"""
    preferred = {
        "basic-solid": ("electric-mining-drill", "burner-mining-drill"),
        "basic-fluid": ("pumpjack",),
    }
    out: dict[str, str] = {}
    for row in conn.execute(
        "SELECT entity_name, resource_categories FROM snap_extractor WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchall():
        raw_cats = row["resource_categories"]
        if not raw_cats:
            continue
        try:
            cats = json.loads(raw_cats)
        except json.JSONDecodeError:
            continue
        entity = row["entity_name"]
        for cat in cats:
            cat = str(cat)
            if cat in out:
                continue
            prefs = preferred.get(cat, ())
            if entity in prefs:
                out[cat] = entity
            elif cat not in out:
                out[cat] = entity
    for cat, prefs in preferred.items():
        if cat not in out:
            for name in prefs:
                out[cat] = name
                break
    return out


def _insert_synthetic_extract_recipes(
    conn,
    snapshot_id: int,
    locale: str,
    resource_id_by_key: dict[tuple[str, str], int],
    raw: dict[str, Any],
) -> None:
    seen: set[tuple[str, str]] = set()
    for row in conn.execute(
        """
        SELECT resource_kind, resource_name, source_type, extractor_entity, resource_category
        FROM snap_resource_extraction
        WHERE snapshot_id = ?
        GROUP BY resource_kind, resource_name
        ORDER BY resource_kind, resource_name
        """,
        (snapshot_id,),
    ).fetchall():
        kind = row["resource_kind"]
        name = row["resource_name"]
        if (kind, name) in seen:
            continue
        seen.add((kind, name))
        _ensure_resource_row(
            conn,
            snapshot_id,
            kind,
            name,
            raw,
            locale,
            resource_id_by_key,
        )
        source_type = row["source_type"]
        extractor_entity = row["extractor_entity"]
        resource_category = row["resource_category"]
        recipe_name = f"{EXTRACT_RECIPE_PREFIX}{name}"
        category = "pumping" if source_type == "offshore_pump" else "mining"
        cur = conn.execute(
            """
            INSERT INTO snap_recipe
            (snapshot_id, name, category, recipe_type, source_type, extractor_entity,
             resource_category, energy, hidden, expansion, main_product)
            VALUES (?, ?, ?, 'extraction', ?, ?, ?, 1, 1, 'base', ?)
            """,
            (snapshot_id, recipe_name, category, source_type, extractor_entity, resource_category, name),
        )
        recipe_id = int(cur.lastrowid)
        # 使用资源本地化标签，避免显示英文 ID
        item_label_row = conn.execute(
            """
            SELECT label FROM snap_resource_text
            WHERE resource_id = (SELECT id FROM snap_resource WHERE snapshot_id = ? AND name = ? AND kind = ?)
              AND locale = ?
            """,
            (snapshot_id, name, kind, locale),
        ).fetchone()
        item_label = item_label_row["label"] if item_label_row else name
        label = _source_type_label(source_type, extractor_entity, item_label)
        conn.execute(
            "INSERT INTO snap_recipe_text (recipe_id, locale, label) VALUES (?, ?, ?)",
            (recipe_id, locale, label),
        )
        conn.execute(
            """
            INSERT INTO snap_recipe_flow
            (recipe_id, direction, resource_kind, resource_name, amount, ord)
            VALUES (?, 'out', ?, ?, 1, 0)
            """,
            (recipe_id, kind, name),
        )


def _source_type_label(source_type: str, extractor_entity: str | None, item_label: str) -> str:
    """生成 extraction recipe 的本地化标签。"""
    if source_type == "offshore_pump":
        return f"海上泵抽取:{item_label}"
    if source_type == "fluid_well":
        return f"抽油机抽取:{item_label}"
    if source_type == "map_resource":
        if extractor_entity == "burner-mining-drill":
            return f"热能矿机开采:{item_label}"
        if extractor_entity == "big-mining-drill":
            return f"大型矿机开采:{item_label}"
        return f"电动矿机开采:{item_label}"
    if source_type == "catch":
        return f"捕捞:{item_label}"
    if source_type == "tree_harvest":
        return f"砍伐:{item_label}"
    if source_type == "enemy_drop":
        return f"击杀掉落:{item_label}"
    if source_type == "space_platform":
        return f"太空平台采集:{item_label}"
    return f"世界获取:{item_label}"


def _ensure_resource_row(
    conn,
    snapshot_id: int,
    kind: str,
    name: str,
    raw: dict[str, Any],
    locale: str,
    resource_id_by_key: dict[tuple[str, str], int],
) -> None:
    key = (kind, name)
    if key in resource_id_by_key:
        return
    if kind == "fluid":
        proto = (raw.get("fluid") or {}).get(name) or {}
        cur = conn.execute(
            """
            INSERT INTO snap_resource
            (snapshot_id, name, kind, proto_type, item_subgroup, expansion, is_raw, visibility)
            VALUES (?, ?, 'fluid', 'fluid', ?, 'base', 0, 'normal')
            """,
            (snapshot_id, name, proto.get("subgroup")),
        )
    else:
        from core.prototype_loader import _find_prototype, _guess_is_raw

        proto = _find_prototype(raw, name) or {}
        cur = conn.execute(
            """
            INSERT INTO snap_resource
            (snapshot_id, name, kind, proto_type, item_subgroup, expansion, is_raw, visibility)
            VALUES (?, ?, 'item', ?, ?, 'base', ?, 'normal')
            """,
            (
                snapshot_id,
                name,
                str(proto.get("type") or "item"),
                proto.get("subgroup"),
                1 if _guess_is_raw(name, proto) else 0,
            ),
        )
    rid = int(cur.lastrowid)
    resource_id_by_key[key] = rid
    conn.execute(
        "INSERT INTO snap_resource_text (resource_id, locale, label) VALUES (?, ?, ?)",
        (rid, locale, name),
    )


def _delete_synthetic_extract_recipes(conn, snapshot_id: int) -> None:
    rows = conn.execute(
        """
        SELECT id FROM snap_recipe
        WHERE snapshot_id = ? AND (recipe_type = 'extraction' OR name LIKE 'fb-extract:%' OR name LIKE 'extract:%')
        """,
        (snapshot_id,),
    ).fetchall()
    ids = [int(r["id"]) for r in rows]
    if not ids:
        return
    placeholders = ",".join("?" * len(ids))
    conn.execute(f"DELETE FROM snap_recipe_flow WHERE recipe_id IN ({placeholders})", tuple(ids))
    conn.execute(f"DELETE FROM snap_recipe_text WHERE recipe_id IN ({placeholders})", tuple(ids))
    conn.execute(f"DELETE FROM snap_recipe_closure_role WHERE recipe_id IN ({placeholders})", tuple(ids))
    conn.execute(f"DELETE FROM snap_recipe_intrinsic_tag WHERE recipe_id IN ({placeholders})", tuple(ids))
    conn.execute(f"DELETE FROM snap_recipe WHERE id IN ({placeholders})", tuple(ids))


def load_world_extractable_keys(conn, snapshot_id: int) -> set[tuple[str, str]]:
    rows = conn.execute(
        """
        SELECT DISTINCT resource_kind, resource_name
        FROM snap_resource_extraction
        WHERE snapshot_id = ?
        """,
        (snapshot_id,),
    ).fetchall()
    return {(r["resource_kind"], r["resource_name"]) for r in rows}


def load_extraction_expandable(
    conn,
    snapshot_id: int,
    enabled_recipe_names: set[str],
) -> set[str]:
    """存档已解锁对应抽取建筑时，资源可在闭包中展开。"""
    out: set[str] = set()
    for row in conn.execute(
        """
        SELECT DISTINCT resource_name, extractor_entity
        FROM snap_resource_extraction
        WHERE snapshot_id = ?
        """,
        (snapshot_id,),
    ).fetchall():
        entity = row["extractor_entity"]
        if entity and entity in enabled_recipe_names:
            out.add(row["resource_name"])
    return out
