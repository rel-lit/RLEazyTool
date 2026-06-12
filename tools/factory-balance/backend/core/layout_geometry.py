"""布局几何：层沿主流向递进，层内节点垂直于流向排开。

默认主流向 LEFT_TO_RIGHT（Factorio 习惯）：
  layer 0 = 最左供给列，layer N = 最右终端列；
  同层节点沿 Y 轴纵向展开，连线从节点右侧出、左侧入。
"""

from __future__ import annotations

from collections import defaultdict

from models.schemas import Position, PrimaryDirection

# 沿主流向（LR 时为 X，TB 时为 Y）
FLOW_STEP = 168
# 垂直于主流向（LR 时为 Y，TB 时为 X）
CROSS_STEP = 72
# 相邻 layer 错半格（紧凑砖墙式，仅视觉交错不额外拉距）
CROSS_STAGGER = CROSS_STEP / 2
# 仅 spread_cross_positions 测试/遗留用；正式布局不再调用
BACKTRACK_CROSS_EXTRA = 48


def staggered_base_cross(layer_idx: int, row_idx: int) -> float:
    """奇偶 layer 错半格：相邻列同行号不在同一水平线上。"""
    return row_idx * CROSS_STEP + (layer_idx % 2) * CROSS_STAGGER


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


def assign_cross_positions(
    layers: dict[str, int], base_rows: dict[str, int]
) -> dict[str, float]:
    """仅按中间产物 layer + 层内行号定位；SBTO 不参与坐标。"""
    return {
        nid: staggered_base_cross(layers[nid], base_rows.get(nid, 0))
        for nid in layers
    }


def spread_cross_positions(
    layers: dict[str, int],
    base_rows: dict[str, int],
    tap_chains: list[list[str]],
) -> dict[str, float]:
    """按 SBTO 链整体错开垂直位置：回绕段加大间距，同层避免重叠。"""
    cross: dict[str, float] = {
        nid: staggered_base_cross(layers[nid], base_rows.get(nid, 0))
        for nid in layers
    }

    for chain in tap_chains:
        for i in range(1, len(chain)):
            a, b = chain[i - 1], chain[i]
            if a not in layers or b not in layers:
                continue
            la, lb = layers[a], layers[b]
            needed = cross[a] + CROSS_STEP
            if lb <= la:
                needed = cross[a] + CROSS_STEP + BACKTRACK_CROSS_EXTRA
            cross[b] = max(cross.get(b, 0.0), needed)

    by_layer: dict[int, list[str]] = defaultdict(list)
    for nid, layer_idx in layers.items():
        by_layer[layer_idx].append(nid)

    for layer_idx in sorted(by_layer.keys()):
        nids = sorted(by_layer[layer_idx], key=lambda n: cross.get(n, 0.0))
        floor = 0.0
        for nid in nids:
            if cross[nid] < floor:
                cross[nid] = floor
            floor = cross[nid] + CROSS_STEP

    return cross


def node_position(
    layer_idx: int, row_idx: int, direction: PrimaryDirection
) -> Position:
    return node_position_at_cross(
        layer_idx, staggered_base_cross(layer_idx, row_idx), direction
    )


def node_position_at_cross(
    layer_idx: int, cross: float, direction: PrimaryDirection
) -> Position:
    if direction == PrimaryDirection.LEFT_TO_RIGHT:
        return Position(x=(layer_idx + 1) * FLOW_STEP, y=cross)
    return Position(x=cross, y=(layer_idx + 1) * FLOW_STEP)


def flow_ports(direction: PrimaryDirection) -> tuple[str, str]:
    """返回 (source_side, target_side)，供文档与前端对齐。"""
    if direction == PrimaryDirection.LEFT_TO_RIGHT:
        return ("right", "left")
    return ("bottom", "top")
