from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from core.layout_engine import compute_layout
from db.layout_snapshot_store import (
    clear_layout_snapshots,
    delete_layout_snapshot,
    get_layout_snapshot,
    list_layout_snapshots,
    upsert_layout_snapshot,
)
from core.game_session import SESSION
from models.schemas import (
    LayoutComputeRequest,
    LayoutComputeResponse,
    LayoutSnapshotDetail,
    LayoutSnapshotEntry,
    LayoutSnapshotUpsert,
    LayoutSnapshotUpsertResult,
)

router = APIRouter(tags=["layout"])


@router.post("/layout/compute", response_model=LayoutComputeResponse)
def compute(body: LayoutComputeRequest) -> LayoutComputeResponse:
    """阶段 1→6 布局计算；不写入快照（由 Layer P PUT /layout/snapshot 负责）。"""
    return compute_layout(body)


@router.put("/layout/snapshot", response_model=LayoutSnapshotUpsertResult)
@router.post("/layout/snapshot", response_model=LayoutSnapshotUpsertResult)
def snapshot_upsert(body: LayoutSnapshotUpsert) -> LayoutSnapshotUpsertResult:
    from core.layout_engine import _resolve_layout_context

    db = _resolve_layout_context()
    labels = {k: v.label for k, v in db.items.items()}
    row = upsert_layout_snapshot(
        body,
        save_key=SESSION.active_save_key,
        env_key=SESSION.env_key,
        item_labels=labels,
    )
    return LayoutSnapshotUpsertResult.model_validate(row)


@router.get("/layout/history", response_model=list[LayoutSnapshotEntry])
def history_list(limit: int = Query(50, ge=1, le=200)) -> list[LayoutSnapshotEntry]:
    return [LayoutSnapshotEntry.model_validate(row) for row in list_layout_snapshots(limit)]


@router.get("/layout/history/{record_id}", response_model=LayoutSnapshotDetail)
def history_get(record_id: int) -> LayoutSnapshotDetail:
    row = get_layout_snapshot(record_id)
    if row is None:
        raise HTTPException(status_code=404, detail="快照不存在")
    return LayoutSnapshotDetail.model_validate(row)


@router.delete("/layout/history/{record_id}")
def history_delete(record_id: int) -> dict[str, bool]:
    if not delete_layout_snapshot(record_id):
        raise HTTPException(status_code=404, detail="快照不存在")
    return {"ok": True}


@router.delete("/layout/history")
def history_clear() -> dict[str, int]:
    return {"deleted": clear_layout_snapshots()}
