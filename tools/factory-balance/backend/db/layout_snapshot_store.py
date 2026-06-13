"""Layer P：布局快照 upsert 存储（与算法流水线解耦）。"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from db.connection import get_connection
from models.schemas import LayoutComputeRequest, LayoutComputeResponse, LayoutSnapshotUpsert


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_layout_key(
    request: LayoutComputeRequest,
    *,
    save_key: str | None = None,
) -> str:
    """配置指纹：同一产出/供给/scope 对应唯一快照槽位。"""
    payload = {
        "save_key": save_key or "",
        "catalog_mode": request.catalog_mode,
        "supply_mode": request.supply_mode.value,
        "targets": sorted(t.item for t in request.targets),
        "supplied_items": sorted(request.supplied_items),
        "forbidden_items": sorted(request.forbidden_items),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _target_summary(request: LayoutComputeRequest, labels: dict[str, str]) -> str:
    parts = [labels.get(t.item, t.item) for t in request.targets]
    return "、".join(parts) if parts else "（无目标）"


def _positions_json(positions: dict[str, Any]) -> str:
    return json.dumps(positions, sort_keys=True, ensure_ascii=False)


def upsert_layout_snapshot(
    body: LayoutSnapshotUpsert,
    *,
    save_key: str | None = None,
    env_key: str | None = None,
    item_labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    labels = item_labels or {}
    layout_key = body.layout_key or build_layout_key(body.request, save_key=save_key)
    summary = _target_summary(body.request, labels)
    response = body.response
    positions = {k: v.model_dump() for k, v in body.user_positions.items()}
    now = _now_iso()

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id, created_at FROM layout_snapshot WHERE layout_key = ?",
            (layout_key,),
        ).fetchone()
        created_at = existing["created_at"] if existing else now

        conn.execute(
            """
            INSERT INTO layout_snapshot (
                layout_key, save_key, env_key, catalog_mode, supply_mode,
                target_summary, target_count,
                node_count, edge_count, tap_count,
                request_json, response_json, user_positions_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(layout_key) DO UPDATE SET
                save_key = excluded.save_key,
                env_key = excluded.env_key,
                catalog_mode = excluded.catalog_mode,
                supply_mode = excluded.supply_mode,
                target_summary = excluded.target_summary,
                target_count = excluded.target_count,
                node_count = excluded.node_count,
                edge_count = excluded.edge_count,
                tap_count = excluded.tap_count,
                request_json = excluded.request_json,
                response_json = excluded.response_json,
                user_positions_json = excluded.user_positions_json,
                updated_at = excluded.updated_at
            """,
            (
                layout_key,
                save_key,
                env_key,
                body.request.catalog_mode,
                body.request.supply_mode.value,
                summary,
                len(body.request.targets),
                len(response.nodes),
                len(response.edges),
                len(response.tap_orders),
                body.request.model_dump_json(),
                response.model_dump_json(by_alias=True),
                _positions_json(positions),
                created_at,
                now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, layout_key, updated_at FROM layout_snapshot WHERE layout_key = ?",
            (layout_key,),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def list_layout_snapshots(limit: int = 50) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, layout_key, save_key, env_key, catalog_mode, supply_mode,
                   target_summary, target_count, node_count, edge_count, tap_count,
                   created_at, updated_at
            FROM layout_snapshot
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (max(1, min(limit, 200)),),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_layout_snapshot(record_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM layout_snapshot WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["request"] = json.loads(data.pop("request_json"))
        data["response"] = json.loads(data.pop("response_json"))
        data["user_positions"] = json.loads(data.pop("user_positions_json"))
        return data
    finally:
        conn.close()


def delete_layout_snapshot(record_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM layout_snapshot WHERE id = ?", (record_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def clear_layout_snapshots() -> int:
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM layout_snapshot")
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
