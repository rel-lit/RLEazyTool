"""阶段 1：双指针原始树构建 + 分析集。"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from core.original_graph import OriginalGraph
from core.recipe_loader import RecipeDatabase
from models.schemas import SupplyMode


def _ingredient_names(recipe) -> list[str]:
    return [i.name for i in recipe.ingredients if i.type in ("item", "fluid")]


@dataclass
class TreeBuildResult:
    graph: OriginalGraph
    analysis_items: set[str]
    terminals: list[str]
    pseudo_external: set[str]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    impossible: bool = False


@dataclass
class TreeBuildContext:
    db: RecipeDatabase
    data_source: set[str]
    expandable: set[str]
    pure_supply: set[str]
    recipe_assignments: dict[str, str]
    user_supplied: set[str]
    forbidden: set[str]
    supply_mode: SupplyMode
    labels: dict[str, str]


def _can_expand(item: str, ctx: TreeBuildContext) -> bool:
    if item not in ctx.data_source:
        return False
    rname = ctx.recipe_assignments.get(item)
    if rname and rname in ctx.db.recipes:
        return True
    return bool(ctx.db.primary_recipe_names_for(item))


def _world_leaf(item: str, ctx: TreeBuildContext) -> bool:
    if ctx.db.is_baseline_supply(item):
        return True
    if item in ctx.pure_supply and item not in ctx.expandable:
        return True
    return False


def _expand_product(
    graph: OriginalGraph,
    product: str,
    ctx: TreeBuildContext,
    analysis_items: set[str],
) -> str | None:
    if product not in ctx.data_source:
        return f"物品不在当前数据源内: {ctx.labels.get(product, product)}"
    if product not in ctx.expandable:
        return f"当前进度下不可制造: {ctx.labels.get(product, product)}"

    rname = ctx.recipe_assignments.get(product)
    if not rname:
        names = ctx.db.primary_recipe_names_for(product)
        if not names:
            return f"无可用 primary 配方: {ctx.labels.get(product, product)}"
        rname = names[0]
    recipe = ctx.db.recipes.get(rname)
    if recipe is None:
        return f"配方不存在: {rname}"

    node = graph.ensure(product)
    node.recipe_name = rname
    analysis_items.add(product)

    for ing in _ingredient_names(recipe):
        graph.add_dependency(ing, product)
    return None


def _resolve_leaf(
    item: str,
    ctx: TreeBuildContext,
) -> tuple[str, str | None]:
    if item in ctx.forbidden:
        if _can_expand(item, ctx):
            return "expand", None
        return (
            "fail",
            f"无法构建树：「{ctx.labels.get(item, item)}」已禁止作为外源且无法通过配方展开",
        )

    if item in ctx.user_supplied:
        return "stop_true", None

    if ctx.supply_mode == SupplyMode.DIRECT:
        return "stop_pseudo", None

    if item in ctx.expandable and _can_expand(item, ctx):
        if _world_leaf(item, ctx):
            return "stop_true", None
        return "expand", None

    if _world_leaf(item, ctx):
        return "stop_true", None

    if _can_expand(item, ctx):
        return "expand", None

    return "stop_true", None


def _build_single_tree(
    root: str,
    ctx: TreeBuildContext,
    analysis_items: set[str],
    pseudo_external: set[str],
    terminals: list[str],
    warnings: list[str],
    built_items: set[str],
) -> tuple[OriginalGraph | None, list[str]]:
    errors: list[str] = []
    graph = OriginalGraph()
    graph.terminals = [root]
    nroot = graph.ensure(root)
    nroot.is_terminal = True
    analysis_items.add(root)

    err = _expand_product(graph, root, ctx, analysis_items)
    if err:
        return None, [err]

    resolved: set[str] = set()
    frontier: deque[str] = deque(
        ing for ing in graph.nodes[root].children
    )

    while frontier:
        item = frontier.popleft()
        if item in resolved:
            continue

        if item in terminals and item != root:
            if item in built_items:
                continue
            try:
                terminals.remove(item)
            except ValueError:
                pass
            warnings.append(
                f"「{ctx.labels.get(item, item)}」被「{ctx.labels.get(root, root)}」"
                f"依赖，已从终端列表移除"
            )
            resolved.add(item)
            continue

        action, leaf_err = _resolve_leaf(item, ctx)
        if leaf_err:
            errors.append(leaf_err)
            break
        if action == "fail":
            errors.append(f"无法构建树：「{ctx.labels.get(item, item)}」")
            break

        if action in ("stop_true", "stop_pseudo"):
            node = graph.ensure(item)
            node.is_external_leaf = True
            analysis_items.add(item)
            if action == "stop_pseudo":
                node.is_pseudo_external = True
                pseudo_external.add(item)
            resolved.add(item)
            continue

        err = _expand_product(graph, item, ctx, analysis_items)
        if err:
            errors.append(err)
            break
        resolved.add(item)
        for ing in graph.nodes[item].children:
            if ing not in resolved:
                frontier.append(ing)

    if errors:
        return None, errors
    return graph, []


def build_original_forest(
    declared_terminals: list[str],
    ctx: TreeBuildContext,
) -> TreeBuildResult:
    terminals = list(dict.fromkeys(declared_terminals))
    analysis_items: set[str] = set()
    pseudo_external: set[str] = set()
    warnings: list[str] = []
    errors: list[str] = []
    forest = OriginalGraph()
    built_roots: set[str] = set()

    for root in list(terminals):
        if root not in terminals:
            continue
        if root in built_roots:
            continue
        if root not in ctx.data_source:
            errors.append(f"产出物不在当前数据源内: {ctx.labels.get(root, root)}")
            continue

        subgraph, tree_errors = _build_single_tree(
            root,
            ctx,
            analysis_items,
            pseudo_external,
            terminals,
            warnings,
            set(forest.nodes.keys()),
        )
        if tree_errors:
            errors.extend(tree_errors)
            break
        if subgraph is None:
            continue
        forest.merge_from(subgraph)
        built_roots.add(root)

    final_terminals = [t for t in terminals if t in forest.nodes]
    for t in final_terminals:
        forest.nodes[t].is_terminal = True
    forest.terminals = final_terminals

    impossible = bool(errors)
    return TreeBuildResult(
        graph=forest,
        analysis_items=analysis_items,
        terminals=final_terminals,
        pseudo_external=pseudo_external,
        warnings=warnings,
        errors=errors,
        impossible=impossible,
    )
