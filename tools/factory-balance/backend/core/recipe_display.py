"""配方可读摘要：供布局 analysis 与前端检视详情使用。"""

from __future__ import annotations

from typing import Any

from core.recipe_loader import Recipe, RecipeDatabase

EXTRACT_PREFIX = "fb-extract:"


def _fmt_amount(amount: float) -> str:
    if abs(amount - round(amount)) < 1e-6:
        return str(int(round(amount)))
    return f"{amount:g}"


def format_recipe_line(recipe: Recipe, labels: dict[str, str]) -> str:
    ing_parts: list[str] = []
    for ing in recipe.ingredients:
        if ing.type not in ("item", "fluid"):
            continue
        lbl = labels.get(ing.name, ing.name)
        ing_parts.append(f"{lbl}×{_fmt_amount(ing.amount)}")

    prod_parts: list[str] = []
    for prod in recipe.products:
        if prod.type not in ("item", "fluid"):
            continue
        lbl = labels.get(prod.name, prod.name)
        prod_parts.append(f"{lbl}×{_fmt_amount(prod.amount)}")

    if not ing_parts and not prod_parts:
        return recipe.label or recipe.name
    if not ing_parts:
        return " → ".join(prod_parts)
    if not prod_parts:
        return " + ".join(ing_parts)
    return f"{' + '.join(ing_parts)} → {' + '.join(prod_parts)}"


def build_recipe_details(
    recipe_assignments: dict[str, str],
    db: RecipeDatabase,
    analysis_items: set[str] | list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    labels = {k: v.label for k, v in db.items.items()}
    details: dict[str, dict[str, Any]] = {}

    for item, rname in recipe_assignments.items():
        item_label = labels.get(item, item)
        recipe = db.recipes.get(rname)

        if rname.startswith(EXTRACT_PREFIX):
            details[item] = {
                "recipe_name": rname,
                "label": item_label,
                "line": f"世界抽取 → {item_label}",
                "kind": "extract",
            }
            continue

        if recipe is None:
            details[item] = {
                "recipe_name": rname,
                "label": item_label,
                "line": rname,
                "kind": "unknown",
            }
            continue

        details[item] = {
            "recipe_name": rname,
            "label": recipe.label or item_label,
            "line": format_recipe_line(recipe, labels),
            "kind": "craft",
        }

    # 分析集内、无制造指派的外源叶子 → 世界开采（铁矿/铜矿/煤等 baseline）
    if analysis_items:
        assigned = set(recipe_assignments.keys())
        for item in analysis_items:
            if item in details:
                continue
            if item in assigned:
                continue
            if not (db.is_baseline_supply(item) or db.is_pure_supply_default(item)):
                continue
            item_label = labels.get(item, item)
            details[item] = {
                "recipe_name": "",
                "label": item_label,
                "line": f"世界开采 → {item_label}",
                "kind": "world-supply",
            }

    return details
