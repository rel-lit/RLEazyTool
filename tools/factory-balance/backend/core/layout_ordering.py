"""合并原始树：层内小数排序 → 整数 rank；cross 与 SBTO 共用 intra_layer_rank。"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from core.layout_geometry import CROSS_STEP


@dataclass
class MergedLayerOrdering:
    """节点在合并图上的两种等级 + 画布 cross。"""

    cross: dict[str, float]
    intra_layer_rank: dict[str, int]
    intra_layer_frac: dict[str, float]


def _sibling_offsets(count: int) -> list[float]:
    """n 个子节点：0, 1/n, 2/n, …, (n-1)/n。"""
    if count <= 0:
        return []
    if count == 1:
        return [0.0]
    step = 1.0 / count
    return [k * step for k in range(count)]


def _build_reverse_adjacency(
    product_edges: list[tuple[str, str]],
) -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = defaultdict(list)
    for src, dst in product_edges:
        reverse[dst].append(src)
    return reverse


def _tree_reachable(
    root_id: str,
    reverse_adj: dict[str, list[str]],
    layers: dict[str, int],
) -> set[str]:
    seen: set[str] = {root_id}
    queue: deque[str] = deque([root_id])
    while queue:
        consumer = queue.popleft()
        for pred in reverse_adj.get(consumer, []):
            if pred not in layers or pred in seen:
                continue
            seen.add(pred)
            queue.append(pred)
    return seen


def assign_merged_layer_ordering(
    layers: dict[str, int],
    product_edges: list[tuple[str, str]],
    terminal_node_ids: list[str],
) -> MergedLayerOrdering:
    """
    按层自上而下（终端 → 原料）：

    1. 终端层根节点小数种子 = 1（根为 1）
    2. 父节点层内整数 rank + 子偏移 k/n 写入下一层的小数桶
    3. 合并图重复节点对小数取平均
    4. 该层排序后赋整数 intra_layer_rank = 1, 2, 3…
    5. 小数仅用于当层合并；跨层只传递已整型化的 rank
    """
    if not layers:
        return MergedLayerOrdering({}, {}, {})

    reverse_adj = _build_reverse_adjacency(product_edges)
    terms = [t for t in terminal_node_ids if t in layers]
    max_layer = max(layers.values())
    if not terms:
        terms = [n for n, li in layers.items() if li == max_layer]

    trees = [
        (root, _tree_reachable(root, reverse_adj, layers))
        for root in terms
    ]

    by_layer: dict[int, list[str]] = defaultdict(list)
    for nid, li in layers.items():
        by_layer[li].append(nid)

    intra_layer_rank: dict[str, int] = {}
    intra_layer_frac: dict[str, float] = {}

    for li in sorted(by_layer.keys(), reverse=True):
        frac_acc: dict[str, list[float]] = defaultdict(list)

        if li == max_layer:
            if trees:
                for root, _reach in trees:
                    if layers.get(root) == li:
                        frac_acc[root].append(1.0)
            else:
                for nid in by_layer[li]:
                    frac_acc[nid].append(1.0)
        else:
            upper = li + 1
            for root, reach in trees:
                for consumer in by_layer.get(upper, []):
                    if consumer not in reach or consumer not in intra_layer_rank:
                        continue
                    base = float(intra_layer_rank[consumer])
                    preds = sorted(
                        p
                        for p in reverse_adj.get(consumer, [])
                        if p in reach and layers.get(p) == li
                    )
                    if not preds:
                        continue
                    offsets = _sibling_offsets(len(preds))
                    for k, pred in enumerate(preds):
                        frac_acc[pred].append(base + offsets[k])

        merged: dict[str, float] = {}
        for nid in by_layer[li]:
            if frac_acc[nid]:
                merged[nid] = sum(frac_acc[nid]) / len(frac_acc[nid])
            else:
                merged[nid] = float(len(by_layer[li]))

        ordered = sorted(by_layer[li], key=lambda n: (merged[n], n))
        for i, nid in enumerate(ordered, start=1):
            intra_layer_rank[nid] = i
            intra_layer_frac[nid] = merged[nid]

    cross: dict[str, float] = {}
    for li in sorted(by_layer.keys()):
        for nid in by_layer[li]:
            cross[nid] = (intra_layer_rank[nid] - 1) * CROSS_STEP

    if cross:
        mid = sum(cross.values()) / len(cross)
        for nid in cross:
            cross[nid] -= mid

    return MergedLayerOrdering(
        cross=cross,
        intra_layer_rank=intra_layer_rank,
        intra_layer_frac=intra_layer_frac,
    )


def assign_cross_merged_tree_ranks(
    layers: dict[str, int],
    product_edges: list[tuple[str, str]],
    terminal_node_ids: list[str],
) -> tuple[dict[str, float], dict[str, int], dict[str, float]]:
    """兼容：返回 (cross, intra_layer_rank, intra_layer_frac)。"""
    result = assign_merged_layer_ordering(layers, product_edges, terminal_node_ids)
    return result.cross, result.intra_layer_rank, result.intra_layer_frac


def assign_cross_merged_tree(
    layers: dict[str, int],
    product_edges: list[tuple[str, str]],
    terminal_node_ids: list[str],
    *,
    sweeps: int = 12,
) -> dict[str, float]:
    result = assign_merged_layer_ordering(layers, product_edges, terminal_node_ids)
    return result.cross


def align_cross_sbto_chains(
    cross: dict[str, float],
    layers: dict[str, int],
    tap_chains: list[tuple[str, list[str]]],
    *,
    step: float = CROSS_STEP,
    backtrack_extra: float = 56.0,
) -> dict[str, float]:
    return cross


def assign_rows_merged_layout(
    layers: dict[str, int],
    product_edges: list[tuple[str, str]],
    terminal_node_ids: list[str],
    *,
    sweeps: int = 6,
) -> dict[str, int]:
    result = assign_merged_layer_ordering(layers, product_edges, terminal_node_ids)
    return {nid: r - 1 for nid, r in result.intra_layer_rank.items()}
