"""Factorio dump → game_snapshot ETL。"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.factorio_paths import load_paths
from core.locale_loader import ensure_locale_cache, load_locale_from_install, merge_locale_tables
from core.prototype_loader import (
    EXTRA_ITEM_TABLES,
    _find_prototype,
    _guess_expansion,
    _guess_is_raw,
    _is_layout_recipe,
    _locale_label,
    _stack_list,
)
from db.connection import get_connection

SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "data" / "snapshots"


def _locale_tables(mod_names: list[str], locale: str) -> dict[str, Any]:
    paths = load_paths()
    merged, _ = ensure_locale_cache(paths, mod_names=mod_names)
    install = load_locale_from_install(paths, mod_names=mod_names, locale=locale)
    return merge_locale_tables(merged, install)


def _visibility(name: str) -> str:
    if name.startswith("parameter-"):
        return "internal"
    return "normal"


def ingest_dump_file(
    dump_path: Path,
    *,
    locale: str = "zh-CN",
    mod_names: list[str] | None = None,
) -> tuple[int, str]:
    """写入 game_snapshot 及子表。返回 (snapshot_id, content_sha256)。"""
    raw_bytes = dump_path.read_bytes()
    content_sha = hashlib.sha256(raw_bytes).hexdigest()
    raw = json.loads(raw_bytes.decode("utf-8"))
    locale_data = _locale_tables(mod_names or [], locale)

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM game_snapshot WHERE content_sha256 = ?", (content_sha,)
        ).fetchone()
        if existing:
            return int(existing["id"]), content_sha

        dest_dir = SNAPSHOTS_DIR / content_sha[:16]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_dump = dest_dir / "data-raw-dump.json"
        if not dest_dump.is_file():
            shutil.copy2(dump_path, dest_dump)

        now = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO game_snapshot (content_sha256, source_path, created_at)
            VALUES (?, ?, ?)
            """,
            (content_sha, str(dest_dump), now),
        )
        snapshot_id = int(cur.lastrowid)

        items: dict[str, dict[str, Any]] = {}
        for name, proto in (raw.get("item") or {}).items():
            if isinstance(proto, dict) and not name.startswith("parameter-"):
                items[name] = proto
        for table in EXTRA_ITEM_TABLES:
            for name, proto in (raw.get(table) or {}).items():
                if isinstance(proto, dict) and not name.startswith("parameter-") and name not in items:
                    items[name] = {**proto, "_table": table}

        fluids = {n: p for n, p in (raw.get("fluid") or {}).items() if isinstance(p, dict)}
        recipes_raw: dict[str, Any] = {}
        for name, proto in (raw.get("recipe") or {}).items():
            if isinstance(proto, dict) and _is_layout_recipe(name, proto):
                recipes_raw[name] = proto

        item_count = 0
        fluid_count = 0
        resource_id_by_key: dict[tuple[str, str], int] = {}

        for name, proto in items.items():
            ptype = str(proto.get("_table") or proto.get("type") or "item")
            vis = _visibility(name)
            cur = conn.execute(
                """
                INSERT INTO snap_resource
                (snapshot_id, name, kind, proto_type, item_group, item_subgroup,
                 expansion, icon, is_raw, visibility)
                VALUES (?, ?, 'item', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    name,
                    ptype,
                    proto.get("item_group"),
                    proto.get("subgroup"),
                    _guess_expansion(name, raw),
                    str(proto.get("icon")) if proto.get("icon") else None,
                    1 if _guess_is_raw(name, proto) else 0,
                    vis,
                ),
            )
            rid = int(cur.lastrowid)
            resource_id_by_key[("item", name)] = rid
            label = _locale_label(locale_data, "item", name, name)
            conn.execute(
                "INSERT INTO snap_resource_text (resource_id, locale, label) VALUES (?, ?, ?)",
                (rid, locale, label),
            )
            item_count += 1

        for name in fluids:
            cur = conn.execute(
                """
                INSERT INTO snap_resource (snapshot_id, name, kind, expansion, is_raw, visibility)
                VALUES (?, ?, 'fluid', ?, 0, 'normal')
                """,
                (snapshot_id, name, _guess_expansion(name, raw)),
            )
            rid = int(cur.lastrowid)
            resource_id_by_key[("fluid", name)] = rid
            label = _locale_label(locale_data, "fluid", name, name)
            conn.execute(
                "INSERT INTO snap_resource_text (resource_id, locale, label) VALUES (?, ?, ?)",
                (rid, locale, label),
            )
            fluid_count += 1

        recipe_id_by_name: dict[str, int] = {}
        recipe_count = 0
        for name, proto in recipes_raw.items():
            category = str(proto.get("category") or "crafting")
            conn.execute(
                "INSERT OR IGNORE INTO meta_recipe_category (code, label_zh) VALUES (?, ?)",
                (category, category),
            )
            products = _stack_list(proto.get("results") or proto.get("products"))
            item_products = [p for p in products if p.type == "item"]
            main_product = proto.get("main_product") or (item_products[0].name if item_products else None)
            cur = conn.execute(
                """
                INSERT INTO snap_recipe
                (snapshot_id, name, category, energy, hidden, expansion, main_product)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    name,
                    category,
                    float(proto.get("energy") or proto.get("energy_required") or 0.5),
                    1 if proto.get("hidden") else 0,
                    _guess_expansion(name, raw),
                    str(main_product) if main_product else None,
                ),
            )
            recipe_id = int(cur.lastrowid)
            recipe_id_by_name[name] = recipe_id
            label = _locale_label(locale_data, "recipe", name, str(main_product or name))
            conn.execute(
                "INSERT INTO snap_recipe_text (recipe_id, locale, label) VALUES (?, ?, ?)",
                (recipe_id, locale, label),
            )

            for ord_i, stack in enumerate(_stack_list(proto.get("ingredients"))):
                conn.execute(
                    """
                    INSERT INTO snap_recipe_flow
                    (recipe_id, direction, resource_kind, resource_name, amount, ord)
                    VALUES (?, 'in', ?, ?, ?, ?)
                    """,
                    (recipe_id, stack.type, stack.name, stack.amount, ord_i),
                )
            for ord_i, stack in enumerate(products):
                conn.execute(
                    """
                    INSERT INTO snap_recipe_flow
                    (recipe_id, direction, resource_kind, resource_name, amount, ord)
                    VALUES (?, 'out', ?, ?, ?, ?)
                    """,
                    (recipe_id, stack.type, stack.name, stack.amount, ord_i),
                )
            recipe_count += 1

        _ensure_recipe_referenced_items(conn, snapshot_id, raw, locale_data, locale, resource_id_by_key)

        stats: dict[int, tuple[int, int]] = {}
        for row in conn.execute(
            """
            SELECT rf.recipe_id, rf.direction, rf.resource_kind, rf.resource_name
            FROM snap_recipe_flow rf
            JOIN snap_recipe r ON r.id = rf.recipe_id
            WHERE r.snapshot_id = ?
            """,
            (snapshot_id,),
        ).fetchall():
            key = (row["resource_kind"], row["resource_name"])
            rid = resource_id_by_key.get(key)
            if rid is None:
                continue
            out, inp = stats.get(rid, (0, 0))
            if row["direction"] == "out":
                stats[rid] = (out + 1, inp)
            else:
                stats[rid] = (out, inp + 1)

        for rid, (out_c, in_c) in stats.items():
            conn.execute(
                """
                INSERT INTO snap_resource_stats (snapshot_id, resource_id, recipes_as_output, recipes_as_input)
                VALUES (?, ?, ?, ?)
                """,
                (snapshot_id, rid, out_c, in_c),
            )

        conn.execute(
            """
            UPDATE game_snapshot SET item_count = ?, recipe_count = ?, fluid_count = ?
            WHERE id = ?
            """,
            (item_count, recipe_count, fluid_count, snapshot_id),
        )
        conn.commit()
        return snapshot_id, content_sha
    finally:
        conn.close()


def _ensure_recipe_referenced_items(
    conn,
    snapshot_id: int,
    raw: dict[str, Any],
    locale_data: dict[str, Any],
    locale: str,
    resource_id_by_key: dict[tuple[str, str], int],
) -> None:
    needed: set[tuple[str, str]] = set()
    for row in conn.execute(
        """
        SELECT rf.resource_kind, rf.resource_name
        FROM snap_recipe_flow rf
        JOIN snap_recipe r ON r.id = rf.recipe_id
        WHERE r.snapshot_id = ? AND rf.resource_kind = 'item'
        """,
        (snapshot_id,),
    ).fetchall():
        key = (row["resource_kind"], row["resource_name"])
        if key not in resource_id_by_key:
            needed.add(key)

    for kind, name in needed:
        if name.startswith("parameter-"):
            continue
        proto = _find_prototype(raw, name) or {}
        vis = _visibility(name)
        cur = conn.execute(
            """
            INSERT INTO snap_resource
            (snapshot_id, name, kind, proto_type, item_subgroup, expansion, is_raw, visibility)
            VALUES (?, ?, 'item', ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                name,
                str(proto.get("type") or "item"),
                proto.get("subgroup"),
                _guess_expansion(name, raw),
                1 if _guess_is_raw(name, proto) else 0,
                vis,
            ),
        )
        rid = int(cur.lastrowid)
        resource_id_by_key[("item", name)] = rid
        label = _locale_label(locale_data, "item", name, name)
        conn.execute(
            "INSERT INTO snap_resource_text (resource_id, locale, label) VALUES (?, ?, ?)",
            (rid, locale, label),
        )


def find_snapshot_by_sha(content_sha256: str) -> int | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM game_snapshot WHERE content_sha256 = ?", (content_sha256,)
        ).fetchone()
        return int(row["id"]) if row else None
    finally:
        conn.close()
