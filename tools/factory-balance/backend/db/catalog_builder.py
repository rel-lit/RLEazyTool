"""物化 catalog_build / catalog_tag（规则 v2）。"""

from __future__ import annotations

from datetime import datetime, timezone

from db.connection import get_connection
from db.extraction_etl import load_extraction_expandable
from db.intrinsic.constants import IR_CONTAINER_BARREL, IR_EXTRACTABLE

TAG_RULE_VERSION = 3


def _gate_recipe_ids(conn, snapshot_id: int, scope_kind: str, scope_key: str) -> set[int]:
    if scope_kind == "environment":
        rows = conn.execute(
            "SELECT id FROM snap_recipe WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchall()
        return {int(r["id"]) for r in rows}
    rows = conn.execute(
        "SELECT recipe_id FROM save_recipe_gate WHERE save_key = ?", (scope_key,)
    ).fetchall()
    return {int(r["recipe_id"]) for r in rows}


def _resource_ir_tags(conn, snapshot_id: int) -> dict[int, set[str]]:
    out: dict[int, set[str]] = {}
    for row in conn.execute(
        """
        SELECT resource_id, tag_code FROM snap_resource_intrinsic_tag
        WHERE snapshot_id = ?
        """,
        (snapshot_id,),
    ).fetchall():
        rid = int(row["resource_id"])
        out.setdefault(rid, set()).add(row["tag_code"])
    return out


def _gate_output_sets(
    conn, gate_ids: set[int]
) -> tuple[set[str], set[str], set[str], set[str]]:
    """primary_out, logistics_out, used_input, all_out names."""
    if not gate_ids:
        return set(), set(), set(), set()
    placeholders = ",".join("?" * len(gate_ids))
    primary_out: set[str] = set()
    logistics_out: set[str] = set()
    used_input: set[str] = set()
    all_out: set[str] = set()

    rows = conn.execute(
        f"""
        SELECT rf.direction, rf.resource_name, cr.closure_role
        FROM snap_recipe_flow rf
        JOIN snap_recipe_closure_role cr ON cr.recipe_id = rf.recipe_id
        WHERE rf.recipe_id IN ({placeholders})
          AND rf.resource_kind IN ('item', 'fluid')
        """,
        tuple(gate_ids),
    ).fetchall()

    for row in rows:
        name = row["resource_name"]
        if row["direction"] == "in":
            used_input.add(name)
        else:
            all_out.add(name)
            if row["closure_role"] == "primary":
                primary_out.add(name)
            elif row["closure_role"] == "logistics":
                logistics_out.add(name)

    logistics_only = logistics_out - primary_out
    return primary_out, logistics_only, used_input, all_out


def compute_scope_resource_names(
    *,
    scope_kind: str,
    scope_key: str,
    env_key: str,
) -> tuple[set[str], set[str], set[str]]:
    """返回 (data_source D, closure_expandable, pure_supply)。"""
    conn = get_connection()
    try:
        env = conn.execute(
            "SELECT snapshot_id FROM game_environment WHERE env_key = ?", (env_key,)
        ).fetchone()
        if not env:
            return set(), set(), set()
        snapshot_id = int(env["snapshot_id"])
        gate_ids = _gate_recipe_ids(conn, snapshot_id, scope_kind, scope_key)
        primary_out, logistics_only, used_input, all_out = _gate_output_sets(conn, gate_ids)

        ir_by_rid = _resource_ir_tags(conn, snapshot_id)
        name_by_rid = {
            int(r["id"]): r["name"]
            for r in conn.execute(
                "SELECT id, name FROM snap_resource WHERE snapshot_id = ?",
                (snapshot_id,),
            ).fetchall()
        }
        baseline: set[str] = set()
        barrel_items: set[str] = set()
        for rid, tags in ir_by_rid.items():
            name = name_by_rid.get(rid)
            if not name:
                continue
            if IR_EXTRACTABLE in tags:
                baseline.add(name)
            if IR_CONTAINER_BARREL in tags:
                barrel_items.add(name)

        closure_expandable = set(primary_out)
        if scope_kind == "save":
            enabled_names = {
                r["name"]
                for r in conn.execute(
                    """
                    SELECT sr.name FROM save_recipe_gate g
                    JOIN snap_recipe sr ON sr.id = g.recipe_id
                    WHERE g.save_key = ?
                    """,
                    (scope_key,),
                ).fetchall()
            }
            closure_expandable |= load_extraction_expandable(conn, snapshot_id, enabled_names)
        else:
            closure_expandable |= {
                r["resource_name"]
                for r in conn.execute(
                    "SELECT DISTINCT resource_name FROM snap_resource_extraction WHERE snapshot_id = ?",
                    (snapshot_id,),
                ).fetchall()
            }
        pure_supply = {n for n in baseline if n not in closure_expandable}

        if scope_kind == "save":
            data_source = closure_expandable | used_input | pure_supply | baseline
        else:
            rows = conn.execute(
                """
                SELECT sr.name, sr.visibility,
                       COALESCE(st.recipes_as_output, 0) AS out_c,
                       COALESCE(st.recipes_as_input, 0) AS in_c
                FROM snap_resource sr
                LEFT JOIN snap_resource_stats st
                  ON st.snapshot_id = sr.snapshot_id AND st.resource_id = sr.id
                WHERE sr.snapshot_id = ?
                """,
                (snapshot_id,),
            ).fetchall()
            data_source = {
                r["name"]
                for r in rows
                if r["visibility"] == "normal" and (r["out_c"] > 0 or r["in_c"] > 0)
            }
            data_source |= closure_expandable | used_input

        return data_source, closure_expandable & data_source, pure_supply & data_source
    finally:
        conn.close()


def build_catalog(*, scope_kind: str, scope_key: str, env_key: str) -> int:
    conn = get_connection()
    try:
        env = conn.execute(
            "SELECT snapshot_id FROM game_environment WHERE env_key = ?", (env_key,)
        ).fetchone()
        if not env:
            raise ValueError(f"unknown environment: {env_key}")
        snapshot_id = int(env["snapshot_id"])
        gate_ids = _gate_recipe_ids(conn, snapshot_id, scope_kind, scope_key)
        primary_out, logistics_only, used_input, _all_out = _gate_output_sets(conn, gate_ids)
        closure_expandable_names = set(primary_out)
        if scope_kind == "save":
            enabled_names = {
                r["name"]
                for r in conn.execute(
                    """
                    SELECT sr.name FROM save_recipe_gate g
                    JOIN snap_recipe sr ON sr.id = g.recipe_id
                    WHERE g.save_key = ?
                    """,
                    (scope_key,),
                ).fetchall()
            }
            closure_expandable_names |= load_extraction_expandable(conn, snapshot_id, enabled_names)
        else:
            closure_expandable_names |= {
                r["resource_name"]
                for r in conn.execute(
                    "SELECT DISTINCT resource_name FROM snap_resource_extraction WHERE snapshot_id = ?",
                    (snapshot_id,),
                ).fetchall()
            }
        ir_by_rid = _resource_ir_tags(conn, snapshot_id)

        rows = conn.execute(
            """
            SELECT sr.id, sr.name, sr.kind, sr.visibility,
                   COALESCE(st.recipes_as_output, 0) AS out_c,
                   COALESCE(st.recipes_as_input, 0) AS in_c
            FROM snap_resource sr
            LEFT JOIN snap_resource_stats st
              ON st.snapshot_id = sr.snapshot_id AND st.resource_id = sr.id
            WHERE sr.snapshot_id = ?
            """,
            (snapshot_id,),
        ).fetchall()

        if scope_kind == "save":
            scope_names = primary_out | used_input | logistics_only
            for r in rows:
                tags = ir_by_rid.get(int(r["id"]), set())
                if IR_EXTRACTABLE in tags:
                    scope_names.add(r["name"])
        else:
            scope_names = {
                r["name"]
                for r in rows
                if r["visibility"] == "normal" and (r["out_c"] > 0 or r["in_c"] > 0)
            }

        tags_by_resource: dict[int, set[str]] = {}
        for r in rows:
            name = r["name"]
            rid = int(r["id"])
            if name not in scope_names:
                continue

            ir_tags = ir_by_rid.get(rid, set())
            vis = r["visibility"]
            tags: set[str] = set()

            if vis == "internal":
                tags.add("internal")
                tags_by_resource[rid] = tags
                continue

            is_baseline = IR_EXTRACTABLE in ir_tags
            is_barrel = IR_CONTAINER_BARREL in ir_tags
            is_primary = name in primary_out
            is_logistics_only = name in logistics_only
            is_input = name in used_input
            closure_expandable = name in closure_expandable_names

            if r["out_c"] > 0:
                tags.add("producible")
            if r["in_c"] > 0:
                tags.add("consumable")
            if is_primary or (closure_expandable and is_baseline):
                tags.add("craftable")
            if is_logistics_only:
                tags.add("craftable_logistics_only")
            if is_input:
                tags.add("used_as_input")
            if is_baseline:
                tags.add("baseline_supply")
            if is_baseline and not closure_expandable:
                tags.add("pure_supply")
            if closure_expandable:
                tags.add("closure_expandable")
            if closure_expandable and is_input:
                tags.add("intermediate")
            if closure_expandable and not is_input:
                tags.add("terminal")
            if closure_expandable and not is_barrel and vis == "normal":
                tags.add("manufacture")
            is_terminal = closure_expandable and not is_input
            if vis == "normal" and not is_terminal and (is_baseline or is_input):
                tags.add("supply")

            if tags:
                tags_by_resource[rid] = tags

        now = datetime.now(timezone.utc).isoformat()
        existing = conn.execute(
            "SELECT id FROM catalog_build WHERE scope_kind = ? AND scope_key = ?",
            (scope_kind, scope_key),
        ).fetchone()
        if existing:
            build_id = int(existing["id"])
            conn.execute("DELETE FROM catalog_tag WHERE build_id = ?", (build_id,))
            conn.execute(
                "UPDATE catalog_build SET env_key = ?, rule_version = ?, built_at = ? WHERE id = ?",
                (env_key, TAG_RULE_VERSION, now, build_id),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO catalog_build (scope_kind, scope_key, env_key, rule_version, built_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (scope_kind, scope_key, env_key, TAG_RULE_VERSION, now),
            )
            build_id = int(cur.lastrowid)

        conn.executemany(
            "INSERT INTO catalog_tag (build_id, resource_id, tag_code) VALUES (?, ?, ?)",
            [(build_id, rid, tag) for rid, tset in tags_by_resource.items() for tag in tset],
        )
        conn.commit()
        return build_id
    finally:
        conn.close()
