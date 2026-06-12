"""产线分析：数据源闭包、配方联合优化、有效终端、建图。"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from core.graph_builder import ProductionGraph, ProductionNode, SupplyNode, _node_id, _supply_id
from core.recipe_loader import RecipeDatabase
from models.schemas import SupplyMode


def _default_recipe_for(product: str, db: RecipeDatabase) -> str:
    names = db.recipes_by_product.get(product, [])
    if not names:
        raise KeyError(product)
    return names[0]


@dataclass
class AnalysisSummary:
    effective_terminals: list[str] = field(default_factory=list)
    declared_outputs: list[str] = field(default_factory=list)
    demoted_outputs: list[str] = field(default_factory=list)
    pseudo_pure_sources: list[str] = field(default_factory=list)
    true_pure_sources: list[str] = field(default_factory=list)
    analysis_items: list[str] = field(default_factory=list)
    recipe_assignments: dict[str, str] = field(default_factory=dict)
    impossible: bool = False


@dataclass
class AnalysisResult:
    graph: ProductionGraph
    effective_terminals: list[str]
    summary: AnalysisSummary
    warnings: list[str] = field(default_factory=list)


def is_manufacturable(name: str, db: RecipeDatabase, craftable_in_d: set[str]) -> bool:
    return name in craftable_in_d and bool(db.recipes_by_product.get(name))


def _ingredient_names(recipe) -> list[str]:
    return [i.name for i in recipe.ingredients if i.type in ("item", "fluid")]


def _craftable_products_in_closure(
    roots: list[str],
    db: RecipeDatabase,
    data_source: set[str],
    craftable_in_d: set[str],
    recipe_pick: dict[str, str] | None = None,
) -> set[str]:
    pick = dict(recipe_pick or {})
    queue = [r for r in roots if r in data_source]
    seen: set[str] = set()
    while queue:
        product = queue.pop()
        if product in seen or product not in data_source:
            continue
        seen.add(product)
        if not is_manufacturable(product, db, craftable_in_d):
            continue
        rname = pick.get(product) or _default_recipe_for(product, db)
        if rname not in db.recipes:
            continue
        for ing in _ingredient_names(db.recipes[rname]):
            if ing in data_source:
                queue.append(ing)
    return {p for p in seen if is_manufacturable(p, db, craftable_in_d)}


def _closure_size(
    roots: list[str],
    recipe_pick: dict[str, str],
    db: RecipeDatabase,
    data_source: set[str],
    craftable_in_d: set[str],
) -> int:
    _, state = build_production_graph(
        roots=roots,
        recipe_pick=recipe_pick,
        mode=SupplyMode.RAW,
        user_supplied=set(),
        forbidden=set(),
        db=db,
        data_source=data_source,
        craftable_in_d=craftable_in_d,
    )
    return 10**9 if state.errors else len(state.analysis_items)


def _pick_recipe_assignments(
    roots: list[str],
    db: RecipeDatabase,
    data_source: set[str],
    craftable_in_d: set[str],
) -> dict[str, str]:
    products = _craftable_products_in_closure(roots, db, data_source, craftable_in_d)
    base = {p: _default_recipe_for(p, db) for p in products if db.recipes_by_product.get(p)}

    choice_lists: dict[str, list[str]] = {}
    for p in sorted(products):
        names = db.recipes_by_product.get(p, [])
        if len(names) > 1:
            choice_lists[p] = names

    if not choice_lists:
        return base

    keys = sorted(choice_lists.keys())
    option_lists = [choice_lists[k] for k in keys]
    total = 1
    for opts in option_lists:
        total *= len(opts)

    best_map = dict(base)
    best_size = _closure_size(roots, best_map, db, data_source, craftable_in_d)
    max_enum = 512

    if total <= max_enum:
        for combo in itertools.product(*option_lists):
            trial = dict(base)
            trial.update(zip(keys, combo))
            sz = _closure_size(roots, trial, db, data_source, craftable_in_d)
            if sz < best_size:
                best_size = sz
                best_map = trial
    else:
        for p in keys:
            for rname in choice_lists[p]:
                trial = dict(best_map)
                trial[p] = rname
                sz = _closure_size(roots, trial, db, data_source, craftable_in_d)
                if sz < best_size:
                    best_size = sz
                    best_map = trial

    return best_map


def _product_depends_on(
    product: str,
    ingredient: str,
    recipe_pick: dict[str, str],
    db: RecipeDatabase,
    cache: dict[tuple[str, str], bool],
) -> bool:
    key = (product, ingredient)
    if key in cache:
        return cache[key]
    if product == ingredient:
        cache[key] = True
        return True
    rname = recipe_pick.get(product)
    if not rname or rname not in db.recipes:
        cache[key] = False
        return False
    for ing in _ingredient_names(db.recipes[rname]):
        if ing == ingredient or _product_depends_on(ing, ingredient, recipe_pick, db, cache):
            cache[key] = True
            return True
    cache[key] = False
    return False


def compute_effective_terminals(
    declared: list[str],
    recipe_pick: dict[str, str],
    db: RecipeDatabase,
) -> tuple[list[str], list[str]]:
    cache: dict[tuple[str, str], bool] = {}
    effective: list[str] = []
    demoted: list[str] = []
    for g in declared:
        dominated = any(
            r != g and _product_depends_on(r, g, recipe_pick, db, cache) for r in declared
        )
        if dominated:
            demoted.append(g)
        else:
            effective.append(g)
    return effective, demoted


@dataclass
class _ClosureState:
    analysis_items: set[str] = field(default_factory=set)
    true_pure: set[str] = field(default_factory=set)
    pseudo_pure: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)
    graph: ProductionGraph = field(default_factory=ProductionGraph)


def build_production_graph(
    *,
    roots: list[str],
    recipe_pick: dict[str, str],
    mode: SupplyMode,
    user_supplied: set[str],
    forbidden: set[str],
    db: RecipeDatabase,
    data_source: set[str],
    craftable_in_d: set[str],
) -> tuple[ProductionGraph, _ClosureState]:
    state = _ClosureState()
    resolved: set[str] = set()
    resolving: set[str] = set()

    def label_for(name: str) -> str:
        return db.items[name].label if name in db.items else name

    def fail(msg: str) -> None:
        if msg not in state.errors:
            state.errors.append(msg)

    def add_supply(name: str, *, pseudo: bool) -> None:
        state.analysis_items.add(name)
        if pseudo:
            state.pseudo_pure.add(name)
        else:
            state.true_pure.add(name)
        if name not in state.graph.supplies:
            state.graph.supplies[name] = SupplyNode(
                id=_supply_id(name),
                item=name,
                label=label_for(name),
            )

    def resolve_material(name: str, *, allow_pseudo: bool) -> None:
        if name in resolved:
            return
        if name in resolving:
            return
        if name not in data_source:
            fail(f"物品不在当前数据源内: {name}")
            return
        if name in forbidden:
            fail(f"已禁止外部供给: {name}")
            return

        resolving.add(name)
        if name in user_supplied:
            add_supply(name, pseudo=False)
        elif mode == SupplyMode.DIRECT and allow_pseudo:
            add_supply(name, pseudo=True)
        elif mode == SupplyMode.RAW:
            if is_manufacturable(name, db, craftable_in_d):
                manufacture(name)
            else:
                add_supply(name, pseudo=False)
        else:
            add_supply(name, pseudo=True)
        resolving.discard(name)
        resolved.add(name)

    def manufacture(product: str) -> None:
        if product in resolved:
            return
        if product not in data_source:
            fail(f"物品不在当前数据源内: {product}")
            return
        if product in forbidden:
            fail(f"已禁止外部供给: {product}")
            return
        if not is_manufacturable(product, db, craftable_in_d):
            fail(f"当前数据源内不可制造: {product}")
            return

        rname = recipe_pick.get(product) or db.recipes_by_product[product][0]
        recipe = db.recipes[rname]
        state.analysis_items.add(product)
        node = ProductionNode(
            id=_node_id(rname),
            recipe_name=rname,
            product=product,
            label=label_for(product),
            inputs=_ingredient_names(recipe),
            outputs=[p.name for p in recipe.products if p.type in ("item", "fluid")],
        )
        state.graph.producers[node.id] = node
        for ing in _ingredient_names(recipe):
            resolve_material(ing, allow_pseudo=True)
        resolved.add(product)

    for root in roots:
        if root not in data_source:
            fail(f"产出物不在当前数据源内: {root}")
            continue
        if is_manufacturable(root, db, craftable_in_d):
            manufacture(root)
        else:
            fail(f"产出物在当前数据源内不可制造: {root}")

    return state.graph, state


def run_analysis(
    *,
    declared_outputs: list[str],
    supply_mode: SupplyMode,
    user_supplied: list[str],
    forbidden: list[str],
    db: RecipeDatabase,
    data_source: set[str],
    craftable_in_d: set[str],
) -> AnalysisResult:
    warnings: list[str] = []
    summary = AnalysisSummary(declared_outputs=list(declared_outputs))
    u_sup = set(user_supplied) - set(forbidden)
    u_forbid = set(forbidden)
    u_out = list(dict.fromkeys(declared_outputs))
    labels = {k: v.label for k, v in db.items.items()}

    if not u_out:
        return AnalysisResult(
            graph=ProductionGraph(),
            effective_terminals=[],
            summary=summary,
            warnings=["请至少选择一个产出物"],
        )

    for name in u_sup:
        if name not in data_source:
            warnings.append(f"已知供给「{labels.get(name, name)}」不在当前数据源内")
    for name in u_forbid:
        if name in user_supplied:
            warnings.append(f"「{labels.get(name, name)}」已禁止供给（覆盖已知供给标记）")

    recipe_pick = _pick_recipe_assignments(u_out, db, data_source, craftable_in_d)
    summary.recipe_assignments = dict(recipe_pick)

    effective, demoted = compute_effective_terminals(u_out, recipe_pick, db)
    summary.effective_terminals = effective
    summary.demoted_outputs = demoted

    for g in demoted:
        warnings.append(
            f"「{labels.get(g, g)}」在产出列表中，但因同时生产其他更高级产出，不作为有效终端；"
            f"可能无对外盈余，不会为其单独建立对外产线"
        )

    graph, state = build_production_graph(
        roots=u_out,
        recipe_pick=recipe_pick,
        mode=supply_mode,
        user_supplied=u_sup,
        forbidden=u_forbid,
        db=db,
        data_source=data_source,
        craftable_in_d=craftable_in_d,
    )

    summary.analysis_items = sorted(state.analysis_items)
    summary.true_pure_sources = sorted(state.true_pure)
    summary.pseudo_pure_sources = sorted(state.pseudo_pure)

    if state.errors:
        summary.impossible = True
        if any("已禁止" in e for e in state.errors):
            warnings.insert(0, "在禁止供给约束下无法实现所选产出，请取消禁止或调整产出目标")
        warnings.extend(state.errors)
        return AnalysisResult(
            graph=ProductionGraph(),
            effective_terminals=effective,
            summary=summary,
            warnings=warnings,
        )

    if supply_mode == SupplyMode.DIRECT and state.pseudo_pure:
        names = "、".join(labels.get(n, n) for n in sorted(state.pseudo_pure))
        warnings.append(
            f"直接产物模式：以下物品被假定为由外部直接提供（未在已知供给中声明）：{names}"
        )

    return AnalysisResult(
        graph=graph,
        effective_terminals=effective,
        summary=summary,
        warnings=warnings,
    )
