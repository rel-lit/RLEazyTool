"""自平衡取用顺序 (SBTO) 计算。"""

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
) -> list[TapOrderResult]:
    shared_items = _find_shared_items(graph)
    results: list[TapOrderResult] = []

    for item in sorted(shared_items):
        consumers = graph.consumers_of(item)
        if len(consumers) < 2:
            continue

        order, rule = _compute_sbto(item, consumers, graph, sink_items)
        results.append(
            TapOrderResult(
                item=item,
                order=order,
                rule=rule,
                explanation=_explain(item, order, rule, consumers, graph, item_labels),
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
    sink_items: list[str],
) -> tuple[list[str], str]:
    gate_order = _rule_b_gate_order(shared_item, consumers, graph)
    if gate_order is not None:
        return gate_order, "rule_b_gate"

    return _rule_a_downstream_order(consumers, graph, sink_items), "rule_a_downstream"


def _rule_b_gate_order(
    shared_item: str,
    consumers: list[ProductionNode],
    graph: ProductionGraph,
) -> list[str] | None:
    """规则 B：若存在“下游产物门控”，被门控者优先 tap。"""
    dag = nx.DiGraph()
    for node in consumers:
        dag.add_node(node.id)

    has_gate_edge = False
    for a in consumers:
        for b in consumers:
            if a.id == b.id:
                continue
            for out in b.outputs:
                if out in a.inputs and out != shared_item:
                    dag.add_edge(a.id, b.id)
                    has_gate_edge = True

    if not has_gate_edge:
        return None

    try:
        ordered = list(nx.topological_sort(dag))
    except nx.NetworkCycleError:
        ordered = [n.id for n in consumers]

    consumer_ids = {n.id for n in consumers}
    return [nid for nid in ordered if nid in consumer_ids]


def _rule_a_downstream_order(
    consumers: list[ProductionNode],
    graph: ProductionGraph,
    sink_items: list[str],
) -> list[str]:
    """规则 A：中间品共享带 —— 越接近最终产出越优先 tap。"""
    dag = nx.DiGraph()
    for node in consumers:
        dag.add_node(node.id)

    consumer_by_product = {n.product: n for n in consumers}
    for a in consumers:
        for b in consumers:
            if a.id == b.id:
                continue
            if b.product in a.inputs:
                dag.add_edge(b.id, a.id)

    for node in consumers:
        if node.product in sink_items:
            dag.add_node(node.id)

    if dag.number_of_edges() == 0:
        return sorted([n.id for n in consumers], key=lambda nid: _node_depth(nid, graph, sink_items), reverse=True)

    try:
        ordered = list(reversed(list(nx.topological_sort(dag))))
    except nx.NetworkCycleError:
        ordered = sorted([n.id for n in consumers], key=lambda nid: _node_depth(nid, graph, sink_items), reverse=True)

    consumer_ids = {n.id for n in consumers}
    seen: list[str] = []
    for nid in ordered:
        if nid in consumer_ids and nid not in seen:
            seen.append(nid)
    for n in consumers:
        if n.id not in seen:
            seen.append(n.id)
    return seen


def _node_depth(
    node_id: str,
    graph: ProductionGraph,
    sink_items: list[str],
    visiting: set[str] | None = None,
) -> int:
    if visiting is None:
        visiting = set()
    if node_id in visiting:
        return 0
    visiting.add(node_id)
    node = graph.producers[node_id]
    if node.product in sink_items:
        visiting.discard(node_id)
        return 100
    depth = 0
    for out in node.outputs:
        for other in graph.producers.values():
            if out in other.inputs:
                depth = max(depth, 1 + _node_depth(other.id, graph, sink_items, visiting))
    visiting.discard(node_id)
    return depth


def _explain(
    item: str,
    order: list[str],
    rule: str,
    consumers: list[ProductionNode],
    graph: ProductionGraph,
    labels: dict[str, str],
) -> str:
    item_label = labels.get(item, item)
    names = [graph.producers[nid].label for nid in order if nid in graph.producers]

    return (
        f"共享物「{item_label}」上，{ ' → '.join(names) }。"
        f"越接近有效终端产出的工厂越优先取用；"
        f"下游因中间品不足而减产时，会释放{item_label}给其它消费者。"
    )
