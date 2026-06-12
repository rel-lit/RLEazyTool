"""统一物品目录：制造目标 / 外部供给 共用数据源，按规则分流。"""

from __future__ import annotations

from dataclasses import dataclass

from .recipe_loader import ItemDef, RecipeDatabase
from .session_cache import filter_player_items, is_internal_item


@dataclass
class ItemCatalog:
    """完整物品表 + 两个 UI 视图。"""

    all_items: list[ItemDef]
    manufacture_items: list[ItemDef]
    supply_items: list[ItemDef]


def _ingredient_names(db: RecipeDatabase) -> set[str]:
    names: set[str] = set()
    for recipe in db.recipes.values():
        for ing in recipe.ingredients:
            if ing.type == "item":
                names.add(ing.name)
    return names


def is_pure_raw(name: str, item: ItemDef, craftable_items: set[str]) -> bool:
    """只能开采/采集、当前存档无法制造的原料。"""
    return name not in craftable_items and item.is_raw


def is_terminal_product(name: str, ingredient_names: set[str]) -> bool:
    """不会作为任何已启用配方的原料（终端产物）。"""
    return name not in ingredient_names


def build_item_catalog(
    db: RecipeDatabase,
    craftable_items: set[str] | None,
) -> ItemCatalog:
    craftable = set(filter_player_items(craftable_items or set()))
    ingredients = _ingredient_names(db)

    names = set(db.items.keys()) | craftable
    names = {n for n in names if not is_internal_item(n)}

    all_items: list[ItemDef] = []
    manufacture: list[ItemDef] = []
    supply: list[ItemDef] = []

    for name in sorted(names, key=lambda n: (db.items.get(n) or ItemDef(n, n)).label):
        item = db.items.get(name) or ItemDef(name=name, label=name, expansion="unknown")
        all_items.append(item)

        if craftable and name in craftable and not is_pure_raw(name, item, craftable):
            manufacture.append(item)
        if not is_terminal_product(name, ingredients):
            supply.append(item)

    return ItemCatalog(
        all_items=all_items,
        manufacture_items=manufacture,
        supply_items=supply,
    )
