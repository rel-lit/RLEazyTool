"""布局坐标与边生成。"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict

from models.schemas import (
    LayoutComputeRequest,
    LayoutComputeResponse,
    LayoutEdge,
    LayoutNode,
    Position,
    TapOrderEntry,
)
from core.analysis_engine import run_analysis
from core.graph_builder import _supply_id
from core.sbto import TapOrderResult, compute_all_tap_orders
from db.data_source import get_data_source_context


LAYER_DX = 220
LAYER_DY = 140
ROW_DY = 100


def _resolve_layout_context():
    from core.game_session import SESSION
    from db.environment_store import list_environments
    from db.recipe_loader_db import load_recipe_database

    if SESSION.env_key and SESSION.active_save_key and SESSION.progress_loaded:
        return load_recipe_database(SESSION.env_key, save_key=SESSION.active_save_key)

    envs = list_environments()
    if envs:
        ek = envs[0]["env_key"]
        return load_recipe_database(ek, save_key=None)

    from core.recipe_loader import load_database

    return load_database()


def compute_layout(request: LayoutComputeRequest) -> LayoutComputeResponse:
    db = _resolve_layout_context()
    data_source, craftable_in_d, _scope = get_data_source_context(
        catalog_mode=request.catalog_mode
    )
    if not data_source:
        data_source = set(db.items.keys())
        craftable_in_d = set(db.recipes_by_product.keys()) & data_source
    item_labels = {k: v.label for k, v in db.items.items()}

    declared = [t.item for t in request.targets]
    analysis = run_analysis(
        declared_outputs=declared,
        supply_mode=request.supply_mode,
        user_supplied=list(request.supplied_items),
        forbidden=list(request.forbidden_items),
        db=db,
        data_source=data_source,
        craftable_in_d=craftable_in_d,
    )

    analysis_meta = asdict(analysis.summary)
    warnings = list(analysis.warnings)

    if analysis.summary.impossible:
        return LayoutComputeResponse(
            nodes=[],
            edges=[],
            tap_orders=[],
            warnings=warnings,
            analysis=analysis_meta,
        )

    graph = analysis.graph
    effective_sinks = analysis.effective_terminals or declared

    tap_results = compute_all_tap_orders(graph, effective_sinks, item_labels)
    layers, layer_warnings = _assign_layers(graph, effective_sinks)
    warnings.extend(layer_warnings)
    nodes = _build_nodes(graph, effective_sinks, layers, item_labels)
    edges = _build_edges(graph, tap_results, layers, item_labels, request)
    tap_orders = _format_tap_orders(tap_results, graph, item_labels)

    return LayoutComputeResponse(
        nodes=nodes,
        edges=edges,
        tap_orders=tap_orders,
        warnings=warnings,
        analysis=analysis_meta,
    )


def _assign_layers(graph, sinks: list[str]) -> tuple[dict[str, int], list[str]]:
    """按依赖拓扑分层；若存在环则降级为扁平布局并给出警告。"""
    warnings: list[str] = []
    layer: dict[str, int] = {}
    for supply in graph.supplies.values():
        layer[supply.id] = 0

    producer_ids = set(graph.producers.keys())
    adj: dict[str, list[str]] = defaultdict(list)
    indeg: dict[str, int] = {nid: 0 for nid in producer_ids}

    for node in graph.producers.values():
        for inp in node.inputs:
            pred = graph.producer_of(inp)
            if pred and pred.id != node.id:
                adj[pred.id].append(node.id)
                indeg[node.id] += 1

    queue = deque(nid for nid in producer_ids if indeg[nid] == 0)
    processed = 0
    while queue:
        nid = queue.popleft()
        processed += 1
        base = layer.get(nid, 0)
        for succ in adj[nid]:
            layer[succ] = max(layer.get(succ, 0), base + 1)
            indeg[succ] -= 1
            if indeg[succ] == 0:
                queue.append(succ)

    if processed < len(producer_ids):
        warnings.append("生产链存在循环依赖，布局已降级为近似分层")
        fallback = max(layer.values()) if layer else 0
        for i, nid in enumerate(sorted(producer_ids)):
            if nid not in layer or nid not in {n for n in layer if n in producer_ids}:
                layer[nid] = fallback + 1 + (i % 3)
            elif processed == 0:
                layer[nid] = 1 + (i % 3)

    for node in graph.producers.values():
        if node.id not in layer:
            preds = []
            for inp in node.inputs:
                pred = graph.producer_of(inp)
                if pred:
                    preds.append(layer.get(pred.id, 0))
                else:
                    preds.append(layer.get(_supply_id(inp), 0))
            layer[node.id] = (max(preds) if preds else 0) + 1

    max_layer = max(layer.values()) if layer else 0
    for node in graph.producers.values():
        if node.product in sinks:
            layer[node.id] = max_layer + 1

    return layer, warnings


def _build_nodes(
    graph,
    sinks: list[str],
    layers: dict[str, int],
    labels: dict[str, str],
) -> list[LayoutNode]:
    nodes: list[LayoutNode] = []
    all_layer_ids: dict[int, list[str]] = defaultdict(list)
    for nid in graph.producers:
        all_layer_ids[layers.get(nid, 0)].append(nid)
    for supply in graph.supplies.values():
        all_layer_ids[layers.get(supply.id, 0)].append(supply.id)

    for layer_idx in sorted(all_layer_ids.keys()):
        ids = all_layer_ids[layer_idx]
        ids.sort(key=lambda x: (0 if x.startswith("supply:") else 1, x))
        for i, nid in enumerate(ids):
            x = (layer_idx + 1) * LAYER_DX
            y = i * ROW_DY
            if nid.startswith("supply:"):
                item = nid.removeprefix("supply:")
                supply = next((s for s in graph.supplies.values() if s.id == nid), None)
                if supply:
                    item = supply.item
                nodes.append(
                    LayoutNode(
                        id=nid,
                        type="supply",
                        item=item,
                        label=labels.get(item, item),
                        layer=layer_idx,
                        position=Position(x=x, y=y),
                        meta={"role": "pure_source"},
                    )
                )
            else:
                prod = graph.producers[nid]
                node_type = "sink" if prod.product in sinks else "producer"
                nodes.append(
                    LayoutNode(
                        id=nid,
                        type=node_type,
                        item=prod.product,
                        label=prod.label,
                        layer=layer_idx,
                        position=Position(x=x, y=y),
                        recipe=prod.recipe_name,
                        meta={"placeholder": "assembler_block"},
                    )
                )

    return nodes


def _build_edges(
    graph,
    tap_results: list[TapOrderResult],
    layers: dict[str, int],
    labels: dict[str, str],
    request: LayoutComputeRequest,
) -> list[LayoutEdge]:
    edges: list[LayoutEdge] = []
    tap_map = {t.item: t for t in tap_results}
    edge_idx = 0

    for node in graph.producers.values():
        for inp in node.inputs:
            edge_idx += 1
            producer = graph.producer_of(inp)
            from_id = producer.id if producer else f"supply:{inp}"
            to_id = node.id
            tap_index = None
            self_balance = False
            rule = None
            edge_type = "belt"
            note = None

            if inp in tap_map and node.id in tap_map[inp].order:
                tap_index = tap_map[inp].order.index(node.id) + 1
                self_balance = True
                rule = tap_map[inp].rule
                belt_order = tap_map[inp].order
                if producer and producer.id in belt_order:
                    prod_idx = belt_order.index(producer.id)
                    cons_idx = belt_order.index(node.id)
                    if request.layout_options.allow_detour and prod_idx > cons_idx:
                        edge_type = "detour"
                        note = f"{labels.get(inp, inp)} 带需绕路：tap 顺序要求先过下游消费者"

            edges.append(
                LayoutEdge(
                    id=f"edge-{edge_idx}",
                    type=edge_type,
                    item=inp,
                    label=labels.get(inp, inp),
                    **{"from": from_id, "to": to_id},
                    tap_index=tap_index,
                    self_balance=self_balance,
                    rule=rule,
                    note=note,
                )
            )

    return edges


def _format_tap_orders(
    tap_results: list[TapOrderResult],
    graph,
    labels: dict[str, str],
) -> list[TapOrderEntry]:
    entries: list[TapOrderEntry] = []
    for tap in tap_results:
        order_labels = [
            graph.producers[nid].label if nid in graph.producers else nid
            for nid in tap.order
        ]
        entries.append(
            TapOrderEntry(
                item=tap.item,
                label=labels.get(tap.item, tap.item),
                order=tap.order,
                order_labels=order_labels,
                rule=tap.rule,
                explanation=tap.explanation,
            )
        )
    return entries
