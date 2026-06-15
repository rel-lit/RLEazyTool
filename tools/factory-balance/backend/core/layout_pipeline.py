"""v2 布局流水线：阶段 1→6 串联。"""

from __future__ import annotations

from core.original_tree import TreeBuildContext, build_original_forest
from core.rank_assigner import assign_ranks
from core.recipe_display import build_recipe_details
from core.recipe_loader import RecipeDatabase, merge_analysis_context
from core.recipe_pick import pick_recipe_assignments, preview_recipe_choices
from core.layout_analysis import build_layout_analysis_meta
from core.layout_renderer import render_layout
from core.sbto import chains_to_tap_results, discover_sbto_chains
from core.tree_layer import build_merged_graph_with_layers
from db.data_source import get_data_source_context
from models.schemas import (
    LayoutComputeRequest,
    LayoutComputeResponse,
    RecipeAssignmentPreviewResponse,
    SupplyMode,
)


def run_layout_pipeline(
    request: LayoutComputeRequest,
    db: RecipeDatabase,
) -> LayoutComputeResponse:
    ctx_ds = get_data_source_context(catalog_mode=request.catalog_mode)
    db = merge_analysis_context(db, ctx_ds)
    data_source = ctx_ds.data_source or set(db.items.keys())
    expandable = set(ctx_ds.closure_expandable) & data_source
    if not expandable:
        expandable = {p for p in data_source if db.primary_recipe_names_for(p)}
    pure_supply = set(db.pure_supply) & data_source

    labels = {k: v.label for k, v in db.items.items()}
    declared = [t.item for t in request.targets]
    warnings: list[str] = []

    if not declared:
        return LayoutComputeResponse(
            nodes=[],
            edges=[],
            tap_orders=[],
            warnings=["请至少选择一个产出物"],
            analysis=build_layout_analysis_meta(
                declared_outputs=[],
                terminals=[],
                analysis_items=[],
                recipe_assignments={},
                pseudo_external=[],
                impossible=False,
            ),
            layout_direction=request.layout_options.primary_direction.value,
        )

    u_sup = set(request.supplied_items) - set(request.forbidden_items)
    u_forbid = set(request.forbidden_items)

    for name in u_sup:
        if name not in data_source:
            warnings.append(f"已知供给「{labels.get(name, name)}」不在当前数据源内")
    for name in u_forbid:
        if name in request.supplied_items:
            warnings.append(
                f"「{labels.get(name, name)}」已禁止供给（覆盖已知供给标记）"
            )

    recipe_assignments, pick_warnings = pick_recipe_assignments(
        declared,
        db,
        data_source,
        expandable,
        request.supply_mode,
        user_assignments=request.recipe_assignments or None,
    )
    warnings.extend(pick_warnings)

    tb_ctx = TreeBuildContext(
        db=db,
        data_source=data_source,
        expandable=expandable,
        pure_supply=pure_supply,
        recipe_assignments=recipe_assignments,
        user_supplied=u_sup,
        forbidden=u_forbid,
        supply_mode=request.supply_mode,
        labels=labels,
    )

    tree_result = build_original_forest(declared, tb_ctx)
    warnings.extend(tree_result.warnings)

    analysis_meta = build_layout_analysis_meta(
        declared_outputs=declared,
        terminals=tree_result.terminals,
        analysis_items=tree_result.analysis_items,
        recipe_assignments=recipe_assignments,
        pseudo_external=tree_result.pseudo_external,
        impossible=tree_result.impossible,
        recipe_details=build_recipe_details(
            recipe_assignments, db, tree_result.analysis_items
        ),
    )

    if tree_result.impossible:
        if any("无法构建" in e or "禁止" in e for e in tree_result.errors):
            warnings.insert(
                0,
                "在禁止供给约束下无法完成原始树构建，请取消禁止或调整产出目标",
            )
        warnings.extend(tree_result.errors)
        return LayoutComputeResponse(
            nodes=[],
            edges=[],
            tap_orders=[],
            warnings=warnings,
            analysis=analysis_meta,
            layout_direction=request.layout_options.primary_direction.value,
        )

    if request.supply_mode == SupplyMode.DIRECT and tree_result.pseudo_external:
        names = "、".join(
            labels.get(n, n) for n in sorted(tree_result.pseudo_external)
        )
        warnings.append(
            f"直接产物模式：以下物品被假定为由外部直接提供（未在已知供给中声明）：{names}"
        )

    graph = build_merged_graph_with_layers(tree_result.graph)
    assign_ranks(graph)
    max_layer = max((n.layer for n in graph.nodes.values()), default=0)
    analysis_meta["max_layer"] = max_layer

    chains = discover_sbto_chains(graph)
    tap_results = chains_to_tap_results(chains, graph, labels)

    nodes, edges, product_edges, hidden_edges, tap_orders = render_layout(
        graph,
        chains,
        tap_results,
        db,
        request.layout_options,
    )

    return LayoutComputeResponse(
        nodes=nodes,
        edges=edges,
        product_edges=product_edges,
        hidden_edges=hidden_edges,
        tap_orders=tap_orders,
        warnings=warnings,
        analysis=analysis_meta,
        layout_direction=request.layout_options.primary_direction.value,
    )


def preview_layout_recipes(
    request: LayoutComputeRequest,
    db: RecipeDatabase,
) -> RecipeAssignmentPreviewResponse:
    """阶段 0：返回本次布局中需要用户确认的配方/来源歧义项。"""
    ctx_ds = get_data_source_context(catalog_mode=request.catalog_mode)
    db = merge_analysis_context(db, ctx_ds)
    data_source = ctx_ds.data_source or set(db.items.keys())
    expandable = set(ctx_ds.closure_expandable) & data_source
    if not expandable:
        expandable = {p for p in data_source if db.primary_recipe_names_for(p)}

    labels = {k: v.label for k, v in db.items.items()}
    declared = [t.item for t in request.targets]
    warnings: list[str] = []

    if not declared:
        return RecipeAssignmentPreviewResponse(ambiguous_items=[], warnings=[])

    u_sup = set(request.supplied_items) - set(request.forbidden_items)

    ambiguous = preview_recipe_choices(
        declared,
        db,
        data_source,
        expandable,
        request.supply_mode,
        labels,
        user_supplied=u_sup,
        user_assignments=request.recipe_assignments or None,
    )
    return RecipeAssignmentPreviewResponse(
        ambiguous_items=ambiguous,
        warnings=warnings,
    )
