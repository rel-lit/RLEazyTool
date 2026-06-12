"""配方与物品加载。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass
class ItemStack:
    name: str
    amount: float
    type: str = "item"


@dataclass
class Recipe:
    name: str
    category: str
    energy: float
    ingredients: list[ItemStack]
    products: list[ItemStack]
    expansion: str = "base"
    label: str = ""


@dataclass
class ItemDef:
    name: str
    label: str
    is_raw: bool = False
    expansion: str = "base"
    group: str | None = None
    kind: str = "item"


@dataclass
class RecipeDatabase:
    items: dict[str, ItemDef]
    recipes: dict[str, Recipe]
    recipes_by_product: dict[str, list[str]] = field(default_factory=dict)

    def default_recipe_for(self, product: str, allowed_recipes: set[str] | None = None) -> Recipe | None:
        names = self.recipes_by_product.get(product, [])
        if allowed_recipes is not None:
            names = [n for n in names if n in allowed_recipes]
        if not names:
            return None
        return self.recipes[names[0]]

    def search(self, query: str = "", expansion: str | None = None) -> tuple[list[ItemDef], list[Recipe]]:
        q = query.strip().lower()
        items = [
            it
            for it in self.items.values()
            if (not expansion or it.expansion == expansion or expansion == "all")
            and (not q or q in it.name.lower() or q in it.label.lower())
        ]
        recipes = [
            r
            for r in self.recipes.values()
            if (not expansion or r.expansion == expansion or expansion == "all")
            and (not q or q in r.name.lower() or q in r.label.lower())
        ]
        items.sort(key=lambda x: x.label)
        recipes.sort(key=lambda x: x.label)
        return items, recipes


def _parse_stack(raw: dict[str, Any]) -> ItemStack:
    return ItemStack(
        name=raw["name"],
        amount=float(raw.get("amount", 1)),
        type=raw.get("type", "item"),
    )


@lru_cache(maxsize=1)
def load_database() -> RecipeDatabase:
    path = DATA_DIR / "recipes.json"
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)

    items: dict[str, ItemDef] = {}
    for raw in payload.get("items", []):
        items[raw["name"]] = ItemDef(
            name=raw["name"],
            label=raw.get("label", raw["name"]),
            is_raw=bool(raw.get("is_raw", False)),
            expansion=raw.get("expansion", "base"),
            group=raw.get("group"),
        )

    recipes: dict[str, Recipe] = {}
    by_product: dict[str, list[str]] = {}
    for raw in payload.get("recipes", []):
        recipe = Recipe(
            name=raw["name"],
            category=raw.get("category", "crafting"),
            energy=float(raw.get("energy", 0.5)),
            ingredients=[_parse_stack(x) for x in raw.get("ingredients", [])],
            products=[_parse_stack(x) for x in raw.get("products", [])],
            expansion=raw.get("expansion", "base"),
            label=raw.get("label", raw["name"]),
        )
        recipes[recipe.name] = recipe
        for prod in recipe.products:
            if prod.type == "item":
                by_product.setdefault(prod.name, []).append(recipe.name)

    return RecipeDatabase(items=items, recipes=recipes, recipes_by_product=by_product)
