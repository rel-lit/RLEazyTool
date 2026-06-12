"""布局坐标与边生成。"""

from __future__ import annotations

from dataclasses import asdict

from models.schemas import (
    LayoutComputeRequest,
    LayoutComputeResponse,
    LayoutEdge,
    LayoutNode,
    PrimaryDirection,
    TapOrderEntry,
)
from core.analysis_engine import run_analysis
from core.graph_builder import _supply_id
from core.sbto import TapOrderResult, compute_all_tap_orders
from core.recipe_loader import merge_analysis_context
from db.data_source import get_data_source_context


from core.layout_geometry import assign_rows_within_layers, node_position


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
    ctx = get_data_source_context(catalog_mode=request.catalog_mode)
    db = merge_analysis_context(db, ctx)
    data_source = ctx.data_source or set(db.items.keys())
    if not ctx.closure_expandable:
        ctx = type(ctx)(
            data_source=data_source,
            closure_expandable={p for p in data_source if db.primary_recipe_names_for(p)},
            pure_supply=set(db.pure_supply) & data_source,
            scope_kind=ctx.scope_kind,
        )
    item_labels = {k: v.label for k, v in db.items.items()}

    declared = [t.item for t in request.targets]
    analysis = run_analysis(
        declared_outputs=declared,
        supply_mode=request.supply_mode,
        user_supplied=list(request.supplied_items),
        forbidden=list(request.forbidden_items),
        db=db,
        data_source=data_source,
        closure_expandable=ctx.closure_expandable,
        pure_supply=ctx.pure_supply,
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
            layout_direction=request.layout_options.primary_direction.value,
        )

    graph = analysis.graph
    effective_sinks = analysis.effective_terminals or declared

    tap_results = compute_all_tap_orders(graph, effective_sinks, item_labels)
    layers, layer_warnings = _assign_layers(graph, effective_sinks)
    warnings.extend(layer_warnings)
    rows = assign_rows_within_layers(layers)
    nodes = _build_nodes(
        graph,
        effective_sinks,
        layers,
        rows,
        item_labels,
        true_pure=set(analysis.summary.true_pure_sources),
        db=db,
        direction=request.layout_options.primary_direction,
    )
    edges = _build_edges(graph, tap_results, layers, item_labels, request)
    tap_orders = _format_tap_orders(tap_results, graph, item_labels)

    return LayoutComputeResponse(
        nodes=nodes,
        edges=edges,
        tap_orders=tap_orders,
        warnings=warnings,
        analysis=analysis_meta,
        layout_direction=request.layout_options.primary_direction.value,
    )


def _assign_layers(graph, sinks: list[str]) -> tuple[dict[str, int], list[str]]:
    """按物料依赖严格分层：任意边 from→to 必有 layer(from) < layer(to)。"""
    warnings: list[str] = []
    layer: dict[str, int] = {}

    for supply in graph.supplies.values():
        layer[supply.id] = 0

    changed = True
    max_iter = len(graph.producers) + len(graph.supplies) + 4
    for _ in range(max_iter):
        if not changed:
            break
        changed = False
        for node in graph.producers.values():
            preds: list[int] = []
            for inp in node.inputs:
                pred = graph.producer_of(inp)
                if pred:
                    preds.append(layer.get(pred.id, 0))
                elif _supply_id(inp) in layer:
                    preds.append(layer[_supply_id(inp)])
            next_layer = (max(preds) if preds else 0) + 1
            if layer.get(node.id, -1) < next_layer:
                layer[node.id] = next_layer
                changed = True

    if len(graph.producers) > 0 and max(layer.get(n.id, 0) for n in graph.producers.values()) <= 1:
        # 检测是否可能存在环（所有 producer 挤在同一层）
        indeg: dict[str, int] = {nid: 0 for nid in graph.producers}
        for node in graph.producers.values():
            for inp in node.inputs:
                pred = graph.producer_of(inp)
                if pred and pred.id != node.id:
                    indeg[node.id] += 1
        if not any(v == 0 for v in indeg.values()) and len(indeg) > 1:
            warnings.append("生产链存在循环依赖，布局已降级为近似分层")
            base = max(layer.values()) if layer else 0
            for i, nid in enumerate(sorted(graph.producers.keys())):
                layer[nid] = base + 1 + (i % 3)

    max_layer = max(layer.values()) if layer else 0
    for node in graph.producers.values():
        if node.product in sinks:
            layer[node.id] = max(max_layer + 1, layer.get(node.id, 0) + 1)

    return layer, warnings


def _build_nodes(
    graph,
    sinks: list[str],
    layers: dict[str, int],
    rows: dict[str, int],
    labels: dict[str, str],
    *,
    true_pure: set[str],
    db,
    direction: PrimaryDirection = PrimaryDirection.LEFT_TO_RIGHT,
) -> list[LayoutNode]:
    nodes: list[LayoutNode] = []
    for nid, layer_idx in layers.items():
        row_idx = rows.get(nid, 0)
        pos = node_position(layer_idx, row_idx, direction)
        if nid.startswith("supply:"):
            item = nid.removeprefix("supply:")
            supply = graph.supplies.get(item) or next(
                (s for s in graph.supplies.values() if s.id == nid), None
            )
            if supply:
                item = supply.item
            is_world = item in true_pure and (
                db.is_baseline_supply(item) if db else False
            )
            nodes.append(
                LayoutNode(
                    id=nid,
                    type="supply",
                    item=item,
                    label=labels.get(item, item),
                    layer=layer_idx,
                    position=pos,
                    meta={
                        "role": "pure_source",
                        "supply_kind": "world_baseline" if is_world else "implicit",
                        "is_pure_source": True,
                    },
                )
            )
        elif nid in graph.producers:
            prod = graph.producers[nid]
            node_type = "sink" if prod.product in sinks else "producer"
            is_extract = prod.recipe_name.startswith("fb-extract:")
            meta: dict = {"placeholder": "assembler_block"}
            if is_extract:
                meta["role"] = "world_extract"
            nodes.append(
                LayoutNode(
                    id=nid,
                    type=node_type,
                    item=prod.product,
                    label=prod.label,
                    layer=layer_idx,
                    position=pos,
                    recipe=prod.recipe_name,
                    meta=meta,
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
    covered: set[tuple[str, str]] = set()

    for item, tap in tap_map.items():
        order = tap.order
        if len(order) < 2:
            continue

        producer = graph.producer_of(item)
        supply_id = _supply_id(item)
        if producer:
            start_id = producer.id
        elif supply_id in layers:
            start_id = supply_id
        else:
            continue

        chain: list[str] = [start_id]
        for nid in order:
            if nid != chain[-1]:
                chain.append(nid)

        belt_order = order
        for i in range(1, len(chain)):
            edge_idx += 1
            from_id = chain[i - 1]
            to_id = chain[i]
            tap_index = i
            edge_type = "tap_chain"
            note = None

            if producer and producer.id in belt_order and to_id in belt_order:
                prod_idx = belt_order.index(producer.id)
                cons_idx = belt_order.index(to_id)
                if request.layout_options.allow_detour and prod_idx > cons_idx:
                    edge_type = "detour"
                    note = (
                        f"{labels.get(item, item)} 带需绕路："
                        f"tap 顺序要求先过下游消费者"
                    )

            edges.append(
                LayoutEdge(
                    id=f"edge-{edge_idx}",
                    type=edge_type,
                    item=item,
                    label=labels.get(item, item),
                    **{"from": from_id, "to": to_id},
                    tap_index=tap_index,
                    self_balance=True,
                    rule=tap.rule,
                    note=note,
                )
            )
            covered.add((item, to_id))

    for node in graph.producers.values():
        for inp in node.inputs:
            if (inp, node.id) in covered:
                continue
            edge_idx += 1
            producer = graph.producer_of(inp)
            from_id = producer.id if producer else f"supply:{inp}"

            edges.append(
                LayoutEdge(
                    id=f"edge-{edge_idx}",
                    type="belt",
                    item=inp,
                    label=labels.get(inp, inp),
                    **{"from": from_id, "to": node.id},
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
