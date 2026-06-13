"""布局计算历史：持久化完整请求/响应快照。

request_json 含 user_layout_before（重算前玩家拖动坐标，不参与算法）。
response_json 语义（一次分析集的可复现包）：
  - nodes：合并产物图节点
      · layer（grade）：结构层级，原料→终端
      · meta.intra_layer_rank：层内整数 1,2,3…
      · meta.intra_layer_frac：当层合并用小数（仅计算用）
  - product_edges：合并原始树的全产物 DAG（无 SBTO 路由）
  - hidden_edges：被 SBTO 替代的反向树实线（悬停时露出）
  - edges：画布可见边 = SBTO 链 (tap_chain/detour) + 剩余 belt
  - tap_orders：每条共享物一条 SBTO 链（消费者 node id 有序列表）
  - analysis：闭包摘要（有效终端、true_pure 等）
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from db.connection import get_connection
from models.schemas import LayoutComputeRequest, LayoutComputeResponse


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _target_summary(request: LayoutComputeRequest, labels: dict[str, str]) -> str:
    parts = [labels.get(t.item, t.item) for t in request.targets]
    return "、".join(parts) if parts else "（无目标）"


def save_layout_history(
    request: LayoutComputeRequest,
    response: LayoutComputeResponse,
    *,
    save_key: str | None = None,
    env_key: str | None = None,
    item_labels: dict[str, str] | None = None,
) -> int:
    labels = item_labels or {}
    summary = _target_summary(request, labels)
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO layout_compute_history (
                save_key, env_key, catalog_mode, supply_mode,
                target_summary, target_count,
                node_count, edge_count, tap_count,
                request_json, response_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                save_key,
                env_key,
                request.catalog_mode,
                request.supply_mode.value,
                summary,
                len(request.targets),
                len(response.nodes),
                len(response.edges),
                len(response.tap_orders),
                request.model_dump_json(),
                response.model_dump_json(by_alias=True),
                _now_iso(),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_layout_history(limit: int = 50) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, save_key, env_key, catalog_mode, supply_mode,
                   target_summary, target_count, node_count, edge_count, tap_count,
                   created_at
            FROM layout_compute_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(limit, 200)),),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_layout_history(record_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM layout_compute_history WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["request"] = json.loads(data.pop("request_json"))
        data["response"] = json.loads(data.pop("response_json"))
        return data
    finally:
        conn.close()


def delete_layout_history(record_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM layout_compute_history WHERE id = ?",
            (record_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def clear_layout_history() -> int:
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM layout_compute_history")
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
