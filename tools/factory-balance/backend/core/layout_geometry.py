"""布局几何：层沿主流向递进，层内节点垂直于流向排开。

默认主流向 LEFT_TO_RIGHT（Factorio 习惯）：
  layer 0 = 最左供给列，layer N = 最右终端列；
  同层节点沿 Y 轴纵向展开，连线从节点右侧出、左侧入。
"""

from __future__ import annotations

from collections import defaultdict

from models.schemas import Position, PrimaryDirection

# 沿主流向（LR 时为 X，TB 时为 Y）
FLOW_STEP = 220
# 垂直于主流向（LR 时为 Y，TB 时为 X）
CROSS_STEP = 100


def assign_rows_within_layers(layers: dict[str, int]) -> dict[str, int]:
    """为每个节点分配层内排位：同 layer 的节点互不重叠。"""
    by_layer: dict[int, list[str]] = defaultdict(list)
    for nid, layer_idx in layers.items():
        by_layer[layer_idx].append(nid)

    rows: dict[str, int] = {}
    for layer_idx in sorted(by_layer.keys()):
        nids = by_layer[layer_idx]
        nids.sort(key=lambda n: (0 if n.startswith("supply:") else 1, n))
        for i, nid in enumerate(nids):
            rows[nid] = i
    return rows


def node_position(
    layer_idx: int, row_idx: int, direction: PrimaryDirection
) -> Position:
    if direction == PrimaryDirection.LEFT_TO_RIGHT:
        return Position(x=(layer_idx + 1) * FLOW_STEP, y=row_idx * CROSS_STEP)
    return Position(x=row_idx * FLOW_STEP, y=(layer_idx + 1) * FLOW_STEP)


def flow_ports(direction: PrimaryDirection) -> tuple[str, str]:
    """返回 (source_side, target_side)，供文档与前端对齐。"""
    if direction == PrimaryDirection.LEFT_TO_RIGHT:
        return ("right", "left")
    return ("bottom", "top")
