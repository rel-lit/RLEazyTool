"""阶段 2–3：layer 初算、树内/跨树合并后的 layer 传播。"""

from __future__ import annotations

from core.original_graph import GraphNode, OriginalGraph


def _leaves(graph: OriginalGraph) -> list[str]:
    return [
        item
        for item, node in graph.nodes.items()
        if not node.children or node.is_external_leaf
    ]


def compute_initial_layers(graph: OriginalGraph) -> None:
    """叶 layer=0，沿 parents 向终端递增，汇合取 max。"""
    for node in graph.nodes.values():
        node.layer = 0

    for leaf in _leaves(graph):
        stack: list[tuple[str, int]] = [(leaf, 0)]
        while stack:
            item, li = stack.pop()
            node = graph.nodes[item]
            node.layer = max(node.layer, li)
            for parent in node.parents:
                stack.append((parent, li + 1))


def enforce_layer_on_edges(graph: OriginalGraph, *, passes: int | None = None) -> None:
    """沿边 child→parent 传播：layer(parent) >= layer(child)+1，取 max 直到稳定。"""
    if not graph.nodes:
        return
    max_layer = max(n.layer for n in graph.nodes.values()) + 4
    n_pass = passes if passes is not None else max(8, max_layer * 2)
    for _ in range(n_pass):
        changed = False
        for item, node in graph.nodes.items():
            for parent in node.parents:
                p = graph.nodes[parent]
                need = node.layer + 1
                if p.layer < need:
                    p.layer = need
                    changed = True
        if not changed:
            break


def merge_graphs(graphs: list[OriginalGraph]) -> OriginalGraph:
    if not graphs:
        return OriginalGraph()
    merged = graphs[0].copy_structure()
    for g in graphs[1:]:
        merged.merge_from(g)
    return merged


def finalize_layers(graph: OriginalGraph) -> OriginalGraph:
    """单图：初算 + 边传播（合并已在 OriginalGraph.merge_from 完成）。"""
    compute_initial_layers(graph)
    enforce_layer_on_edges(graph)
    return graph


def build_merged_graph_with_layers(forest: OriginalGraph) -> OriginalGraph:
    """跨终端森林 → 原始图 G + layer。"""
    g = forest.copy_structure()
    finalize_layers(g)
    g.terminals = list(forest.terminals)
    for t in g.terminals:
        if t in g.nodes:
            g.nodes[t].is_terminal = True
    return g
