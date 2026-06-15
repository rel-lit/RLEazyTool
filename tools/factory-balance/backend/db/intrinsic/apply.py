"""Snapshot ingest 后写入 IR/IP tag 与 primary 图统计。"""

from __future__ import annotations

from db.intrinsic.recipe_classifier import FlowStack, classify_recipe
from db.intrinsic.resource_classifier import classify_resource, params_to_json
from db.extraction_etl import load_world_extractable_keys


def apply_intrinsic_tags(conn, snapshot_id: int, raw: dict | None = None) -> None:
    raw = raw or {}
    world_extractable = load_world_extractable_keys(conn, snapshot_id)
    conn.execute(
        "DELETE FROM snap_resource_intrinsic_tag WHERE snapshot_id = ?",
        (snapshot_id,),
    )
    conn.execute(
        "DELETE FROM snap_recipe_intrinsic_tag WHERE snapshot_id = ?",
        (snapshot_id,),
    )
    conn.execute(
        "DELETE FROM snap_recipe_closure_role WHERE snapshot_id = ?",
        (snapshot_id,),
    )
    conn.execute(
        "DELETE FROM snap_resource_stats_primary WHERE snapshot_id = ?",
        (snapshot_id,),
    )

    resources = conn.execute(
        """
        SELECT id, name, kind, visibility, item_subgroup, is_raw
        FROM snap_resource WHERE snapshot_id = ?
        """,
        (snapshot_id,),
    ).fetchall()

    for row in resources:
        proto = _find_proto(raw, row["name"], row["kind"])
        tags, params, is_raw = classify_resource(
            name=row["name"],
            kind=row["kind"],
            visibility=row["visibility"],
            item_subgroup=row["item_subgroup"],
            proto=proto,
            world_extractable=world_extractable,
        )
        if is_raw != bool(row["is_raw"]):
            conn.execute(
                "UPDATE snap_resource SET is_raw = ? WHERE id = ?",
                (1 if is_raw else 0, row["id"]),
            )
        params_json = params_to_json(params)
        for tag in tags:
            conn.execute(
                """
                INSERT INTO snap_resource_intrinsic_tag
                (snapshot_id, resource_id, tag_code, params_json)
                VALUES (?, ?, ?, ?)
                """,
                (snapshot_id, row["id"], tag, params_json),
            )

    recipes = conn.execute(
        "SELECT id, name, category, recipe_type FROM snap_recipe WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchall()

    primary_recipe_ids: set[int] = set()
    for recipe in recipes:
        rid = int(recipe["id"])
        flows_rows = conn.execute(
            """
            SELECT direction, resource_kind, resource_name
            FROM snap_recipe_flow WHERE recipe_id = ?
            """,
            (rid,),
        ).fetchall()
        flows = [
            FlowStack(name=r["resource_name"], kind=r["resource_kind"], direction=r["direction"])
            for r in flows_rows
        ]
        tags, closure_role = classify_recipe(
            name=recipe["name"],
            category=recipe["category"],
            recipe_type=recipe["recipe_type"],
            flows=flows,
        )
        conn.execute(
            """
            INSERT INTO snap_recipe_closure_role (snapshot_id, recipe_id, closure_role)
            VALUES (?, ?, ?)
            """,
            (snapshot_id, rid, closure_role),
        )
        if closure_role == "primary":
            primary_recipe_ids.add(rid)
        for tag in tags:
            conn.execute(
                """
                INSERT INTO snap_recipe_intrinsic_tag
                (snapshot_id, recipe_id, tag_code, params_json)
                VALUES (?, ?, ?, NULL)
                """,
                (snapshot_id, rid, tag),
            )

    stats: dict[int, tuple[int, int]] = {}
    if primary_recipe_ids:
        placeholders = ",".join("?" * len(primary_recipe_ids))
        for row in conn.execute(
            f"""
            SELECT rf.recipe_id, rf.direction, rf.resource_kind, rf.resource_name
            FROM snap_recipe_flow rf
            WHERE rf.recipe_id IN ({placeholders})
            """,
            tuple(primary_recipe_ids),
        ).fetchall():
            res = conn.execute(
                """
                SELECT id FROM snap_resource
                WHERE snapshot_id = ? AND name = ? AND kind = ?
                """,
                (snapshot_id, row["resource_name"], row["resource_kind"]),
            ).fetchone()
            if not res:
                continue
            resource_id = int(res["id"])
            out_c, in_c = stats.get(resource_id, (0, 0))
            if row["direction"] == "out":
                stats[resource_id] = (out_c + 1, in_c)
            else:
                stats[resource_id] = (out_c, in_c + 1)

    for resource_id, (out_c, in_c) in stats.items():
        conn.execute(
            """
            INSERT INTO snap_resource_stats_primary
            (snapshot_id, resource_id, recipes_as_output_primary, recipes_as_input_primary)
            VALUES (?, ?, ?, ?)
            """,
            (snapshot_id, resource_id, out_c, in_c),
        )


def _find_proto(raw: dict, name: str, kind: str) -> dict:
    if kind == "fluid":
        return (raw.get("fluid") or {}).get(name) or {}
    from core.prototype_loader import _find_prototype

    return _find_prototype(raw, name) or {}
