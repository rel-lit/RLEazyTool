"""布局几何：层沿主流向递进，层内节点垂直于流向排开。

默认主流向 LEFT_TO_RIGHT（Factorio 习惯）：
  layer 0 = 最左供给列，layer N = 最右终端列；
  同层节点沿 Y 轴纵向展开，连线从节点右侧出、左侧入。
"""

from __future__ import annotations

from collections import defaultdict

from models.schemas import Position, PrimaryDirection

# 沿主流向（LR 时为 X，TB 时为 Y）
FLOW_STEP = 192
# 垂直于主流向（LR 时为 Y，TB 时为 X）
CROSS_STEP = 96
# 相邻 layer 错半格（砖墙式交错）
CROSS_STAGGER = CROSS_STEP / 2
# SBTO 回绕链额外拉开间距
BACKTRACK_CROSS_EXTRA = 56


def staggered_base_cross(layer_idx: int, row_idx: int) -> float:
    """奇偶 layer 错半格：相邻列同行号不在同一水平线上。"""
    return row_idx * CROSS_STEP + (layer_idx % 2) * CROSS_STAGGER


def _brick_slot_free(candidate: float, used: list[float]) -> bool:
    return all(abs(candidate - u) >= CROSS_STEP - 1e-6 for u in used)


def _pick_brick_slot(layer_idx: int, preferred: float, used: list[float]) -> float:
    """在砖块格子上选最近可用槽，同层保持 CROSS_STEP 间距。"""
    stagger = (layer_idx % 2) * CROSS_STAGGER
    center_slot = round((preferred - stagger) / CROSS_STEP)

    candidates: list[int] = [center_slot]
    for radius in range(1, 64):
        candidates.extend([center_slot - radius, center_slot + radius])

    for slot in candidates:
        if slot < -2:
            continue
        cross = staggered_base_cross(layer_idx, slot)
        if _brick_slot_free(cross, used):
            return cross

    for slot in range(128):
        cross = staggered_base_cross(layer_idx, slot)
        if _brick_slot_free(cross, used):
            return cross

    return staggered_base_cross(layer_idx, len(used))


def assign_rank_cross_positions(
    layers: dict[str, int],
    intra_layer_rank: dict[str, int],
) -> dict[str, float]:
    """严格按 layer + rank 映射 cross：同层 Y 随 rank 单调递增，仅奇偶层错半格。"""
    if not layers:
        return {}

    cross = {
        nid: staggered_base_cross(li, intra_layer_rank.get(nid, 0))
        for nid, li in layers.items()
    }

    if cross:
        mid = sum(cross.values()) / len(cross)
        for nid in cross:
            cross[nid] -= mid

    return cross


def assign_brick_cross_positions(
    layers: dict[str, int],
    intra_layer_rank: dict[str, int],
    product_edges: list[tuple[str, str]],
) -> dict[str, float]:
    """砖块法插空：奇偶层错半格，同层节点按 rank 顺序占最近空槽（贴近上游 cross）。"""
    if not layers:
        return {}

    reverse_adj: dict[str, list[str]] = defaultdict(list)
    for src, dst in product_edges:
        reverse_adj[dst].append(src)

    by_layer: dict[int, list[str]] = defaultdict(list)
    for nid, li in layers.items():
        by_layer[li].append(nid)

    cross: dict[str, float] = {}
    for li in sorted(by_layer.keys()):
        nids = sorted(
            by_layer[li],
            key=lambda n: (intra_layer_rank.get(n, 0), n),
        )
        used: list[float] = []

        for nid in nids:
            rank = intra_layer_rank.get(nid, 1)
            fallback = staggered_base_cross(li, rank - 1)

            upstream = [
                p
                for p in reverse_adj.get(nid, [])
                if p in cross and layers.get(p, -1) < li
            ]
            if upstream:
                preferred = sum(cross[p] for p in upstream) / len(upstream)
            else:
                preferred = fallback

            slot_cross = _pick_brick_slot(li, preferred, used)
            cross[nid] = slot_cross
            used.append(slot_cross)

    if cross:
        mid = sum(cross.values()) / len(cross)
        for nid in cross:
            cross[nid] -= mid

    return cross


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
