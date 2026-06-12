from __future__ import annotations

from fastapi import APIRouter, Query

from core.layout_engine import compute_layout
from models.schemas import LayoutComputeRequest, LayoutComputeResponse

router = APIRouter(tags=["layout"])


@router.post("/layout/compute", response_model=LayoutComputeResponse)
def compute(body: LayoutComputeRequest) -> LayoutComputeResponse:
    return compute_layout(body)
