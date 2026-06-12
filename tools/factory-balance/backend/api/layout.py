from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from core.game_session import SESSION
from core.layout_engine import compute_layout
from db.layout_history_store import (
    clear_layout_history,
    delete_layout_history,
    get_layout_history,
    list_layout_history,
    save_layout_history,
)
from models.schemas import (
    LayoutComputeRequest,
    LayoutComputeResponse,
    LayoutHistoryDetail,
    LayoutHistoryEntry,
)

router = APIRouter(tags=["layout"])


@router.post("/layout/compute", response_model=LayoutComputeResponse)
def compute(
    body: LayoutComputeRequest,
    save_history: bool = Query(True, description="是否写入布局历史"),
) -> LayoutComputeResponse:
    result = compute_layout(body)
    if save_history and result.nodes and not result.analysis.get("impossible"):
        from core.layout_engine import _resolve_layout_context

        db = _resolve_layout_context()
        labels = {k: v.label for k, v in db.items.items()}
        history_id = save_layout_history(
            body,
            result,
            save_key=SESSION.active_save_key,
            env_key=SESSION.env_key,
            item_labels=labels,
        )
        result.history_id = history_id
    return result


@router.get("/layout/history", response_model=list[LayoutHistoryEntry])
def history_list(limit: int = Query(50, ge=1, le=200)) -> list[LayoutHistoryEntry]:
    return [LayoutHistoryEntry.model_validate(row) for row in list_layout_history(limit)]


@router.get("/layout/history/{record_id}", response_model=LayoutHistoryDetail)
def history_get(record_id: int) -> LayoutHistoryDetail:
    row = get_layout_history(record_id)
    if row is None:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return LayoutHistoryDetail.model_validate(row)


@router.delete("/layout/history/{record_id}")
def history_delete(record_id: int) -> dict[str, bool]:
    if not delete_layout_history(record_id):
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return {"ok": True}


@router.delete("/layout/history")
def history_clear() -> dict[str, int]:
    return {"deleted": clear_layout_history()}
