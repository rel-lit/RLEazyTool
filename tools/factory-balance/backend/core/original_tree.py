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
    recipe_assignments: dict[str, str]   # item -> recipe_name，覆盖模式默认
    user_supplied: set[str]
    forbidden: set[str]
    supply_mode: SupplyMode
    labels: dict[str, str]


def _can_expand(item: str, ctx: TreeBuildContext) -> bool:
    return item in ctx.expandable


def _is_world_leaf(item: str, ctx: TreeBuildContext) -> bool:
    """RAW 模式下可作为世界供给叶子的物品：基线可抽取但当前无法展开。"""
    if not ctx.db.is_world_obtainable(item):
        return False
    if item in ctx.pure_supply:
        return True
    if ctx.db.is_baseline_supply(item) and item not in ctx.expandable:
        return True
    return False


def _choose_recipe(product: str, ctx: TreeBuildContext) -> str | None:
    """按优先级为 item 选一个展开配方。"""
    # P2：用户显式指定 recipe
    if product in ctx.recipe_assignments:
        return ctx.recipe_assignments[product]

    # P1 特化：forbidden 物品必须作为工厂产物展开，不能用采集配方变成世界来源叶子
    if product in ctx.forbidden:
        names = ctx.db.primary_manufacturing_recipe_names_for(product)
        return names[0] if names else None

    # P5：RAW 模式优先用 extraction recipe
    if ctx.supply_mode == SupplyMode.RAW:
        ext = ctx.db.default_extraction_recipe_for(product)
        if ext:
            return ext.name

    # P6：默认 primary recipe（manufacturing 优先）
    names = ctx.db.primary_manufacturing_recipe_names_for(product)
    if names:
        return names[0]

    # fallback：任意 primary（理论上不会走到，因为 extraction 已处理）
    names = ctx.db.primary_recipe_names_for(product)
    return names[0] if names else None


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

    rname = _choose_recipe(product, ctx)
    if rname is None:
        return f"无可用 primary 配方: {ctx.labels.get(product, product)}"
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
    # P1：forbidden 物品不能作为外部叶子，必须用工厂配方展开。
    # 若仅有采集配方（会变成世界来源叶子）或完全无配方，则失败。
    if item in ctx.forbidden:
        if ctx.db.is_factory_obtainable(item):
            return "expand", None
        return (
            "fail",
            f"无法构建树：「{ctx.labels.get(item, item)}」已禁止供给且仅有采集来源/无配方，无法通过工厂配方展开",
        )

    # P0：用户供给 = 外部叶子
    if item in ctx.user_supplied:
        return "stop_true", None

    # P2：用户显式指定了 recipe，按 recipe 展开（覆盖模式默认）
    if item in ctx.recipe_assignments and _can_expand(item, ctx):
        return "expand", None

    # P5/P6：模式默认
    if _can_expand(item, ctx):
        if ctx.supply_mode == SupplyMode.RAW and _is_world_leaf(item, ctx):
            return "stop_true", None
        return "expand", None

    # DIRECT 模式下无法展开的未供给中间产物 = 伪外部供给
    if ctx.supply_mode == SupplyMode.DIRECT:
        return "stop_pseudo", None

    # RAW 模式下无配方也无世界来源 = 世界供给叶子（或 impossible 后续处理）
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
            try:
                terminals.remove(item)
            except ValueError:
                pass
            warnings.append(
                f"「{ctx.labels.get(item, item)}」被「{ctx.labels.get(root, root)}」"
                f"依赖，已从终端列表移除"
            )
            if item in built_items:
                # 另一终端的原始树已并入森林，复用已有子图即可
                graph.nodes[item].is_terminal = False
                resolved.add(item)
                continue
            # 尚未独立建树：降级后继续按普通节点展开/停叶
            graph.nodes[item].is_terminal = False

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
    for node in forest.nodes.values():
        node.is_terminal = False
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
