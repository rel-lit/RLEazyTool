"""自平衡取用顺序 (SBTO) — 与层内整数 rank 一致。"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from .graph_builder import ProductionGraph, ProductionNode


@dataclass
class TapOrderResult:
    item: str
    order: list[str]
    rule: str
    explanation: str


def compute_all_tap_orders(
    graph: ProductionGraph,
    sink_items: list[str],
    item_labels: dict[str, str],
    layers: dict[str, int] | None = None,
    intra_layer_rank: dict[str, int] | None = None,
) -> list[TapOrderResult]:
    shared_items = _find_shared_items(graph)
    results: list[TapOrderResult] = []
    grade = layers or {}
    ranks = intra_layer_rank or {}

    for item in sorted(shared_items):
        consumers = graph.consumers_of(item)
        if len(consumers) < 2:
            continue

        order, rule = _compute_sbto(item, consumers, graph, grade, ranks)
        results.append(
            TapOrderResult(
                item=item,
                order=order,
                rule=rule,
                explanation=_explain(item, order, consumers, graph, item_labels),
            )
        )

    return results


def _find_shared_items(graph: ProductionGraph) -> set[str]:
    counts: dict[str, int] = {}
    for node in graph.producers.values():
        for item in node.inputs:
            counts[item] = counts.get(item, 0) + 1
    return {item for item, n in counts.items() if n >= 2}


def _compute_sbto(
    shared_item: str,
    consumers: list[ProductionNode],
    graph: ProductionGraph,
    layers: dict[str, int],
    intra_layer_rank: dict[str, int],
) -> tuple[list[str], str]:
    return (
        _intra_rank_tap_order(shared_item, consumers, layers, intra_layer_rank),
        "intra_layer_rank",
    )


def _intra_rank_sort(
    node_ids: list[str],
    layers: dict[str, int],
    intra_layer_rank: dict[str, int],
) -> list[str]:
    """等级越高、层内 rank 越小（越靠上）越优先 tap。"""
    return sorted(
        node_ids,
        key=lambda nid: (
            -layers.get(nid, 0),
            intra_layer_rank.get(nid, 999),
            nid,
        ),
    )


def _consumer_tap_dag(
    shared_item: str,
    consumers: list[ProductionNode],
) -> nx.DiGraph:
    dag: nx.DiGraph = nx.DiGraph()
    for node in consumers:
        dag.add_node(node.id)

    for a in consumers:
        deps = {x for x in a.inputs if x != shared_item}
        if not deps:
            continue
        for b in consumers:
            if a.id == b.id:
                continue
            if b.product in deps:
                dag.add_edge(a.id, b.id)
            for out in b.outputs:
                if out in deps and out != b.product:
                    dag.add_edge(a.id, b.id)

    return dag


def _intra_rank_tap_order(
    shared_item: str,
    consumers: list[ProductionNode],
    layers: dict[str, int],
    intra_layer_rank: dict[str, int],
) -> list[str]:
    ids = [n.id for n in consumers]
    dag = _consumer_tap_dag(shared_item, consumers)

    if dag.number_of_edges() == 0:
        return _intra_rank_sort(ids, layers, intra_layer_rank)

    try:
        ordered = list(nx.topological_sort(dag))
    except nx.NetworkCycleError:
        ordered = _intra_rank_sort(ids, layers, intra_layer_rank)

    seen: list[str] = []
    for nid in ordered:
        if nid not in seen:
            seen.append(nid)
    for nid in _intra_rank_sort(ids, layers, intra_layer_rank):
        if nid not in seen:
            seen.append(nid)
    return seen


def _explain(
    item: str,
    order: list[str],
    consumers: list[ProductionNode],
    graph: ProductionGraph,
    labels: dict[str, str],
) -> str:
    item_label = labels.get(item, item)
    names = [graph.producers[nid].label for nid in order if nid in graph.producers]

    return (
        f"共享物「{item_label}」上，{ ' → '.join(names) }。"
        f"与合并图 layer + 层内 rank 一致：等级越高、层内 rank 越小者优先取用；"
        f"门控约束仍优先于同级排序。"
    )
