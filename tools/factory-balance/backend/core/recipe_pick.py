"""多 primary 配方联合优选：最小化分析集物品种类数。"""

from __future__ import annotations

import itertools

from typing import Any

from core.recipe_loader import RecipeDatabase, RecipeType
from models.schemas import SupplyMode


def _ingredient_names(recipe) -> list[str]:
    return [i.name for i in recipe.ingredients if i.type in ("item", "fluid")]


def _default_primary(product: str, db: RecipeDatabase, supply_mode: SupplyMode) -> str:
    """按 supply_mode 选择默认 primary recipe。"""
    if supply_mode == SupplyMode.RAW:
        ext = db.default_extraction_recipe_for(product)
        if ext:
            return ext.name
    names = db.primary_manufacturing_recipe_names_for(product)
    if names:
        return names[0]
    names = db.primary_recipe_names_for(product)
    if names:
        return names[0]
    raise KeyError(product)


def _closure_products(
    roots: list[str],
    recipe_pick: dict[str, str],
    db: RecipeDatabase,
    data_source: set[str],
    expandable: set[str],
    supply_mode: SupplyMode,
) -> set[str]:
    seen: set[str] = set()
    queue = [r for r in roots if r in data_source]
    while queue:
        product = queue.pop()
        if product in seen or product not in data_source:
            continue
        seen.add(product)
        if product not in expandable:
            continue
        rname = recipe_pick.get(product) or _default_primary(product, db, supply_mode)
        if rname not in db.recipes:
            continue
        for ing in _ingredient_names(db.recipes[rname]):
            if ing in data_source:
                queue.append(ing)
    return seen


def pick_recipe_assignments(
    roots: list[str],
    db: RecipeDatabase,
    data_source: set[str],
    expandable: set[str],
    supply_mode: SupplyMode,
    *,
    max_combos: int = 8192,
    user_assignments: dict[str, str] | None = None,
) -> tuple[dict[str, str], list[str]]:
    """返回 (recipe_assignments, warnings)。

    user_assignments: 用户已确认的 item -> recipe 映射；覆盖自动选择结果。
    """
    warnings: list[str] = []
    user_assignments = user_assignments or {}
    products: set[str] = set()
    queue = [r for r in roots if r in data_source]
    seen: set[str] = set()
    while queue:
        p = queue.pop()
        if p in seen or p not in data_source:
            continue
        seen.add(p)
        if p not in expandable:
            continue
        rname = user_assignments.get(p)
        if rname is None:
            try:
                rname = _default_primary(p, db, supply_mode)
            except KeyError:
                continue
        products.add(p)
        for ing in _ingredient_names(db.recipes[rname]):
            if ing in data_source:
                queue.append(ing)

    base = {
        p: user_assignments.get(p) or _default_primary(p, db, supply_mode)
        for p in products
        if db.primary_recipe_names_for(p)
    }

    choice_lists: dict[str, list[str]] = {}
    for p in sorted(products):
        if p in user_assignments:
            continue
        names = db.primary_recipe_names_for(p)
        if len(names) > 1:
            choice_lists[p] = names

    if not choice_lists:
        return base, warnings

    keys = sorted(choice_lists.keys())
    option_lists = [choice_lists[k] for k in keys]
    total = 1
    for opts in option_lists:
        total *= len(opts)
    if total > max_combos:
        warnings.append(
            f"多配方组合过多（{total}），已用默认 primary 配方"
        )
        return base, warnings

    best_pick = base
    best_size = len(_closure_products(roots, base, db, data_source, expandable, supply_mode))

    for combo in itertools.product(*option_lists):
        pick = dict(base)
        for k, rname in zip(keys, combo):
            pick[k] = rname
        size = len(_closure_products(roots, pick, db, data_source, expandable, supply_mode))
        if size < best_size:
            best_size = size
            best_pick = pick

    return best_pick, warnings


def preview_recipe_choices(
    roots: list[str],
    db: RecipeDatabase,
    data_source: set[str],
    expandable: set[str],
    supply_mode: SupplyMode,
    labels: dict[str, str],
    *,
    user_supplied: set[str] | None = None,
    forbidden: set[str] | None = None,
    user_assignments: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """返回需要用户确认的配方选择预览列表。

    每个条目包含：item, label, default_recipe, options[{recipe_name, label, line, kind}]

    user_supplied: 用户已声明为外部供给的物品，不再询问其配方。
    forbidden: 用户禁止作为外部来源的物品；只能用工厂配方展开。
    user_assignments: 用户已确认的 item -> recipe 映射；用于计算级联歧义。
    """
    user_supplied = user_supplied or set()
    forbidden = forbidden or set()
    user_assignments = user_assignments or {}
    root_set = set(roots)
    ambiguous: list[dict[str, Any]] = []
    queue = [r for r in roots if r in data_source]
    seen: set[str] = set()
    while queue:
        p = queue.pop()
        if p in seen or p not in data_source or p in user_supplied:
            continue
        seen.add(p)
        if p not in expandable:
            continue

        # DIRECT 模式：只有终端产物(root) 和 forbidden 才展开；其余未供给物品作为叶子
        if supply_mode == SupplyMode.DIRECT and p not in root_set and p not in forbidden:
            continue

        # forbidden 物品：只能用工厂配方展开；若有多个工厂配方则询问
        if p in forbidden:
            names = db.primary_manufacturing_recipe_names_for(p)
            if len(names) > 1:
                ambiguous.append(_build_ambiguity_entry(p, names, db, labels, supply_mode))
            elif len(names) == 1:
                recipe = db.recipes.get(names[0])
                if recipe is not None:
                    for ing in _ingredient_names(recipe):
                        if ing in data_source:
                            queue.append(ing)
            continue

        # 用户已确认：直接展开
        if p in user_assignments:
            rname = user_assignments[p]
            recipe = db.recipes.get(rname)
            if recipe is None:
                continue
            for ing in _ingredient_names(recipe):
                if ing in data_source:
                    queue.append(ing)
            continue

        names = db.primary_recipe_names_for(p)
        if not names:
            continue

        # 多个 recipe 且未确认：作为当前 frontier 歧义返回，不再继续展开
        # （等用户确认后再决定走哪条分支）
        if len(names) > 1:
            ambiguous.append(_build_ambiguity_entry(p, names, db, labels, supply_mode))
            continue

        # 只有一个 recipe：直接展开
        rname = names[0]
        recipe = db.recipes.get(rname)
        if recipe is None:
            continue
        for ing in _ingredient_names(recipe):
            if ing in data_source:
                queue.append(ing)

    return ambiguous


def _build_ambiguity_entry(
    p: str,
    names: list[str],
    db: RecipeDatabase,
    labels: dict[str, str],
    supply_mode: SupplyMode,
) -> dict[str, Any]:
    default_rname = _default_primary(p, db, supply_mode)
    options: list[dict[str, Any]] = []
    for rname in names:
        recipe = db.recipes.get(rname)
        if recipe is None:
            continue
        options.append({
            "recipe_name": rname,
            "label": recipe.label or rname,
            "line": _format_recipe_line(recipe, labels),
            "kind": recipe.recipe_type.value,
        })
    return {
        "item": p,
        "label": labels.get(p, p),
        "default_recipe": default_rname,
        "options": options,
    }


def _format_recipe_line(recipe, labels: dict[str, str]) -> str:
    def fmt(amount: float) -> str:
        if abs(amount - round(amount)) < 1e-6:
            return str(int(round(amount)))
        return f"{amount:g}"

    if recipe.recipe_type == RecipeType.EXTRACTION:
        prod = next((p for p in recipe.products if p.type in ("item", "fluid")), None)
        if prod:
            return f"世界获取 → {labels.get(prod.name, prod.name)}"
        return recipe.label or recipe.name

    ing_parts = [
        f"{labels.get(ing.name, ing.name)}×{fmt(ing.amount)}"
        for ing in recipe.ingredients
        if ing.type in ("item", "fluid")
    ]
    prod_parts = [
        f"{labels.get(prod.name, prod.name)}×{fmt(prod.amount)}"
        for prod in recipe.products
        if prod.type in ("item", "fluid")
    ]
    if not ing_parts and not prod_parts:
        return recipe.label or recipe.name
    if not ing_parts:
        return " → ".join(prod_parts)
    if not prod_parts:
        return " + ".join(ing_parts)
    return f"{' + '.join(ing_parts)} → {' + '.join(prod_parts)}"
