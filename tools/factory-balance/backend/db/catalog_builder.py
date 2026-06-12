"""物化 catalog_build / catalog_tag。"""

from __future__ import annotations

from datetime import datetime, timezone

from db.connection import get_connection

TAG_RULE_VERSION = 1


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


def _flow_item_sets(conn, gate_ids: set[int]) -> tuple[set[str], set[str]]:
    if not gate_ids:
        return set(), set()
    placeholders = ",".join("?" * len(gate_ids))
    craftable: set[str] = set()
    used_input: set[str] = set()
    for row in conn.execute(
        f"""
        SELECT direction, resource_kind, resource_name
        FROM snap_recipe_flow WHERE recipe_id IN ({placeholders})
        """,
        tuple(gate_ids),
    ).fetchall():
        if row["resource_kind"] not in ("item", "fluid"):
            continue
        name = row["resource_name"]
        if row["direction"] == "out":
            craftable.add(name)
        else:
            used_input.add(name)
    return craftable, used_input


def compute_scope_resource_names(
    *,
    scope_kind: str,
    scope_key: str,
    env_key: str,
) -> tuple[set[str], set[str]]:
    """返回 (data_source D, craftable_in_d)。"""
    conn = get_connection()
    try:
        env = conn.execute(
            "SELECT snapshot_id FROM game_environment WHERE env_key = ?", (env_key,)
        ).fetchone()
        if not env:
            return set(), set()
        snapshot_id = int(env["snapshot_id"])
        gate_ids = _gate_recipe_ids(conn, snapshot_id, scope_kind, scope_key)
        craftable_names, input_names = _flow_item_sets(conn, gate_ids)

        if scope_kind == "save":
            data_source = craftable_names | input_names
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
            data_source |= craftable_names | input_names

        return data_source, craftable_names & data_source
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
        craftable_names, input_names = _flow_item_sets(conn, gate_ids)

        rows = conn.execute(
            """
            SELECT sr.id, sr.name, sr.kind, sr.is_raw, sr.visibility,
                   COALESCE(st.recipes_as_output, 0) AS out_c,
                   COALESCE(st.recipes_as_input, 0) AS in_c
            FROM snap_resource sr
            LEFT JOIN snap_resource_stats st
              ON st.snapshot_id = sr.snapshot_id AND st.resource_id = sr.id
            WHERE sr.snapshot_id = ? AND sr.visibility != 'internal'
            """,
            (snapshot_id,),
        ).fetchall()

        if scope_kind == "save":
            scope_names = craftable_names | input_names
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

            tags: set[str] = set()
            vis = r["visibility"]
            is_raw = bool(r["is_raw"])
            is_craftable = name in craftable_names
            is_input = name in input_names

            if vis == "internal":
                tags.add("internal")
            if is_raw:
                tags.add("raw")
            if r["out_c"] > 0:
                tags.add("producible")
            if r["in_c"] > 0:
                tags.add("consumable")
            if is_craftable:
                tags.add("craftable")
            if is_input:
                tags.add("used_as_input")
            if is_raw and not is_craftable:
                tags.add("pure_raw")
            if not is_input:
                tags.add("terminal")
            if is_craftable and is_input:
                tags.add("intermediate")
            if is_craftable and not (is_raw and not is_craftable) and vis == "normal":
                tags.add("manufacture")
            if vis == "normal" and is_input:
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
