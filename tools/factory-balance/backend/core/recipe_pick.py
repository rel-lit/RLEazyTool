"""多 primary 配方联合优选：最小化分析集物品种类数。"""

from __future__ import annotations

import itertools

from core.recipe_loader import RecipeDatabase


def _ingredient_names(recipe) -> list[str]:
    return [i.name for i in recipe.ingredients if i.type in ("item", "fluid")]


def _default_primary(product: str, db: RecipeDatabase) -> str:
    names = db.primary_recipe_names_for(product)
    if not names:
        raise KeyError(product)
    return names[0]


def _closure_products(
    roots: list[str],
    recipe_pick: dict[str, str],
    db: RecipeDatabase,
    data_source: set[str],
    expandable: set[str],
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
        rname = recipe_pick.get(product) or _default_primary(product, db)
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
    *,
    max_combos: int = 8192,
) -> tuple[dict[str, str], list[str]]:
    """返回 (recipe_assignments, warnings)。"""
    warnings: list[str] = []
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
        try:
            rname = _default_primary(p, db)
        except KeyError:
            continue
        products.add(p)
        for ing in _ingredient_names(db.recipes[rname]):
            if ing in data_source:
                queue.append(ing)

    base = {
        p: _default_primary(p, db)
        for p in products
        if db.primary_recipe_names_for(p)
    }

    choice_lists: dict[str, list[str]] = {}
    for p in sorted(products):
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
    best_size = len(_closure_products(roots, base, db, data_source, expandable))

    for combo in itertools.product(*option_lists):
        pick = dict(base)
        for k, rname in zip(keys, combo):
            pick[k] = rname
        size = len(_closure_products(roots, pick, db, data_source, expandable))
        if size < best_size:
            best_size = size
            best_pick = pick

    return best_pick, warnings
