"""阶段 6：坐标与四类边通道。"""

from __future__ import annotations

from core.layout_geometry import assign_rank_cross_positions, node_position_at_cross
from core.original_graph import OriginalGraph
from core.sbto import SbtoChain, TapOrderResult
from core.recipe_loader import RecipeDatabase
from models.schemas import (
    LayoutEdge,
    LayoutNode,
    LayoutOptions,
    PrimaryDirection,
    TapOrderEntry,
)


def render_layout(
    graph: OriginalGraph,
    chains: list[SbtoChain],
    tap_results: list[TapOrderResult],
    db: RecipeDatabase,
    options: LayoutOptions,
) -> tuple[list[LayoutNode], list[LayoutEdge], list[LayoutEdge], list[LayoutEdge], list[TapOrderEntry]]:
    labels = {k: v.label for k, v in db.items.items()}
    direction = options.primary_direction

    layers = {item: n.layer for item, n in graph.nodes.items()}
    ranks = {item: n.rank for item, n in graph.nodes.items()}
    cross = assign_rank_cross_positions(layers, ranks)

    nodes: list[LayoutNode] = []
    for item, node in graph.nodes.items():
        pos = node_position_at_cross(node.layer, cross.get(item, 0.0), direction)
        meta: dict = {
            "layer": node.layer,
            "rank": node.rank,
            "rank_frac": node.rank_frac,
        }
        if node.is_pseudo_external:
            meta["node_kind"] = "pure_source"
            meta["external_leaf"] = True
            meta["pseudo_external"] = True
        elif node.is_external_leaf:
            meta["node_kind"] = "pure_source"
            meta["external_leaf"] = True
            if db.is_baseline_supply(item):
                meta["supply_kind"] = "world_baseline"
            else:
                meta["supply_kind"] = "user_supplied"
        elif node.is_terminal:
            meta["node_kind"] = "terminal"
            meta["role"] = "terminal"
        else:
            meta["node_kind"] = "intermediate"
        if node.recipe_name:
            meta["recipe"] = node.recipe_name

        nodes.append(
            LayoutNode(
                id=item,
                type="item",
                item=item,
                label=labels.get(item, item),
                layer=node.layer,
                position=pos,
                recipe=node.recipe_name,
                meta=meta,
            )
        )

    product_edges: list[LayoutEdge] = []
    idx = 0
    for ingredient, product in graph.edges():
        idx += 1
        product_edges.append(
            LayoutEdge(
                id=f"product-{idx}",
                type="product",
                item=ingredient,
                label=labels.get(ingredient, ingredient),
                **{"from": ingredient, "to": product},
            )
        )

    chain_by_item = {c.item: c for c in chains}
    visible: list[LayoutEdge] = []
    edge_idx = 0

    for chain in chains:
        order = chain.tap_order
        path = [chain.root] + order
        for i in range(1, len(path)):
            edge_idx += 1
            from_id = path[i - 1]
            to_id = path[i]
            visible.append(
                LayoutEdge(
                    id=f"edge-{edge_idx}",
                    type="tap_chain",
                    item=chain.item,
                    label=labels.get(chain.item, chain.item),
                    **{"from": from_id, "to": to_id},
                    tap_index=i,
                    self_balance=True,
                    rule="layer_rank",
                )
            )

    for pe in product_edges:
        key = (pe.from_node, pe.to_node, pe.item)
        chain = chain_by_item.get(pe.item)
        if chain and pe.to_node in chain.tap_order:
            continue
        edge_idx += 1
        visible.append(
            LayoutEdge(
                id=f"edge-{edge_idx}",
                type="belt",
                item=pe.item,
                label=pe.label,
                **{"from": pe.from_node, "to": pe.to_node},
            )
        )

    hidden: list[LayoutEdge] = []
    hidx = 0
    for pe in product_edges:
        chain = chain_by_item.get(pe.item)
        if not chain or pe.to_node not in chain.tap_order:
            continue
        hidx += 1
        hidden.append(
            LayoutEdge(
                id=f"hidden-{hidx}",
                type="hidden",
                item=pe.item,
                label=pe.label,
                **{"from": pe.from_node, "to": pe.to_node},
            )
        )

    tap_entries: list[TapOrderEntry] = []
    for tap in tap_results:
        tap_entries.append(
            TapOrderEntry(
                item=tap.item,
                label=labels.get(tap.item, tap.item),
                order=tap.order,
                order_labels=[labels.get(x, x) for x in tap.order],
                rule=tap.rule,
                explanation=tap.explanation,
            )
        )

    return nodes, visible, product_edges, hidden, tap_entries
