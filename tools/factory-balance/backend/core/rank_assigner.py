"""阶段 4：rank 分数 + 层内整型 rank。"""

from __future__ import annotations

from collections import defaultdict

from core.original_graph import OriginalGraph


def assign_ranks(graph: OriginalGraph) -> None:
    if not graph.nodes:
        return

    by_layer: dict[int, list[str]] = defaultdict(list)
    for item, node in graph.nodes.items():
        by_layer[node.layer].append(item)

    max_layer = max(by_layer.keys())

    l0 = sorted(by_layer.get(0, []))
    n0 = len(l0) or 1
    for x, item in enumerate(l0, start=1):
        graph.nodes[item].rank_frac = x / n0

    for li in range(1, max_layer + 1):
        for item in by_layer.get(li, []):
            node = graph.nodes[item]
            if not node.children:
                node.rank_frac = 0.0
                continue
            prod = 1.0
            for child in sorted(node.children):
                prod *= graph.nodes[child].rank_frac or 0.0
            node.rank_frac = prod

    for li in range(max_layer + 1):
        items = sorted(by_layer.get(li, []), key=lambda i: (graph.nodes[i].rank_frac, i))
        for rank, item in enumerate(items):
            graph.nodes[item].rank = rank
