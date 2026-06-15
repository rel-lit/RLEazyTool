"""配方与物品加载。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from db.intrinsic.constants import CLOSURE_PRIMARY, IR_CONTAINER_BARREL, IR_EXTRACTABLE
from db.intrinsic.recipe_classifier import classify_bundled_recipe
from db.intrinsic.resource_classifier import classify_resource

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass
class ItemStack:
    name: str
    amount: float
    type: str = "item"


class RecipeType(str, Enum):
    EXTRACTION = "extraction"
    MANUFACTURING = "manufacturing"
    SMELTING = "smelting"
    CHEMISTRY = "chemistry"
    REFINING = "refining"
    LOGISTICS = "logistics"
    ENERGY = "energy"


class SourceType(str, Enum):
    WORLD = "world"
    FACTORY = "factory"


@dataclass
class Recipe:
    name: str
    category: str
    recipe_type: RecipeType = RecipeType.MANUFACTURING
    source_type: str | None = None          # 仅 extraction 有效
    extractor_entity: str | None = None     # 仅 extraction 有效
    resource_category: str | None = None    # 仅 extraction 有效
    location: str | None = None             # 仅 extraction 有效
    base_rate: float | None = None          # 仅 extraction 有效
    energy: float = 0.5
    ingredients: list[ItemStack] = field(default_factory=list)
    products: list[ItemStack] = field(default_factory=list)
    expansion: str = "base"
    label: str = ""

    def __post_init__(self):
        if isinstance(self.recipe_type, str):
            self.recipe_type = RecipeType(self.recipe_type)

    @property
    def is_extraction(self) -> bool:
        return self.recipe_type == RecipeType.EXTRACTION


@dataclass
class ItemDef:
    name: str
    label: str
    is_raw: bool = False
    expansion: str = "base"
    group: str | None = None
    kind: str = "item"
    icon_slug: str | None = None

    def to_item_info(self) -> "ItemInfo":
        """转换为 API 层的 ItemInfo。所有字段映射集中在此处。"""
        from models.schemas import ItemInfo

        return ItemInfo(
            name=self.name,
            label=self.label,
            group=self.group,
            is_raw=self.is_raw,
            expansion=self.expansion,
            icon_slug=self.icon_slug,
        )


@dataclass
class RecipeDatabase:
    items: dict[str, ItemDef]
    recipes: dict[str, Recipe]
    recipes_by_product: dict[str, list[str]] = field(default_factory=dict)
    recipe_closure_role: dict[str, str] = field(default_factory=dict)
    primary_recipes_by_product: dict[str, list[str]] = field(default_factory=dict)
    resource_intrinsic_tags: dict[str, set[str]] = field(default_factory=dict)
    closure_expandable: set[str] = field(default_factory=set)
    pure_supply: set[str] = field(default_factory=set)

    def primary_recipe_names_for(self, product: str, allowed: set[str] | None = None) -> list[str]:
        names = self.primary_recipes_by_product.get(product, [])
        if allowed is not None:
            names = [n for n in names if n in allowed]
        return names

    def primary_extraction_recipe_names_for(self, product: str) -> list[str]:
        return [
            n for n in self.primary_recipe_names_for(product)
            if self.recipes[n].is_extraction
        ]

    def primary_manufacturing_recipe_names_for(self, product: str) -> list[str]:
        return [
            n for n in self.primary_recipe_names_for(product)
            if not self.recipes[n].is_extraction
        ]

    def default_primary_recipe_for(
        self, product: str, allowed_recipes: set[str] | None = None
    ) -> Recipe | None:
        names = self.primary_recipe_names_for(product, allowed_recipes)
        if not names:
            return None
        return self.recipes[names[0]]

    def default_extraction_recipe_for(self, product: str) -> Recipe | None:
        names = self.primary_extraction_recipe_names_for(product)
        if not names:
            return None
        return self.recipes[names[0]]

    def default_manufacturing_recipe_for(self, product: str) -> Recipe | None:
        names = self.primary_manufacturing_recipe_names_for(product)
        if not names:
            return None
        return self.recipes[names[0]]

    def default_recipe_for(self, product: str, allowed_recipes: set[str] | None = None) -> Recipe | None:
        return self.default_primary_recipe_for(product, allowed_recipes)

    def is_closure_expandable(self, name: str) -> bool:
        return name in self.closure_expandable

    def is_pure_supply_default(self, name: str) -> bool:
        return name in self.pure_supply

    def is_baseline_supply(self, name: str) -> bool:
        return IR_EXTRACTABLE in self.resource_intrinsic_tags.get(name, set())

    def is_world_obtainable(self, name: str) -> bool:
        """物品有可用的 extraction primary recipe 即为世界可获取。"""
        return bool(self.primary_extraction_recipe_names_for(name))

    def is_factory_obtainable(self, name: str) -> bool:
        """物品有可用的 manufacturing primary recipe 即为工厂可制造。"""
        return bool(self.primary_manufacturing_recipe_names_for(name))

    def is_barrel_item(self, name: str) -> bool:
        return IR_CONTAINER_BARREL in self.resource_intrinsic_tags.get(name, set())

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


def _finalize_database(
    items: dict[str, ItemDef],
    recipes: dict[str, Recipe],
    by_product: dict[str, list[str]],
    recipe_roles: dict[str, str],
) -> RecipeDatabase:
    resource_tags: dict[str, set[str]] = {}
    for name, item in items.items():
        tags, _, is_raw = classify_resource(
            name=name,
            kind=item.kind,
            visibility="normal",
            item_subgroup=item.group,
            proto={},
        )
        resource_tags[name] = tags
        item.is_raw = is_raw

    primary_by_product: dict[str, list[str]] = {}
    closure_expandable: set[str] = set()
    for rname, recipe in recipes.items():
        role = recipe_roles.get(rname, CLOSURE_PRIMARY)
        for prod in recipe.products:
            if prod.type not in ("item", "fluid"):
                continue
            by_product.setdefault(prod.name, []).append(rname)
            if role == CLOSURE_PRIMARY:
                primary_by_product.setdefault(prod.name, []).append(rname)
                closure_expandable.add(prod.name)

    pure_supply = {
        name
        for name, tags in resource_tags.items()
        if IR_EXTRACTABLE in tags and name not in closure_expandable
    }

    return RecipeDatabase(
        items=items,
        recipes=recipes,
        recipes_by_product=by_product,
        recipe_closure_role=recipe_roles,
        primary_recipes_by_product=primary_by_product,
        resource_intrinsic_tags=resource_tags,
        closure_expandable=closure_expandable,
        pure_supply=pure_supply,
    )


@lru_cache(maxsize=1)
def load_database() -> RecipeDatabase:
    path = DATA_DIR / "recipes.json"
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)

    items: dict[str, ItemDef] = {}
    for raw in payload.get("items", []):
        kind = "fluid" if raw.get("group") == "fluid" else "item"
        items[raw["name"]] = ItemDef(
            name=raw["name"],
            label=raw.get("label", raw["name"]),
            is_raw=bool(raw.get("is_raw", False)),
            expansion=raw.get("expansion", "base"),
            group=raw.get("group"),
            kind=kind,
        )

    recipes: dict[str, Recipe] = {}
    recipe_roles: dict[str, str] = {}
    for raw in payload.get("recipes", []):
        ingredients = [_parse_stack(x) for x in raw.get("ingredients", [])]
        products = [_parse_stack(x) for x in raw.get("products", [])]
        category = raw.get("category", "crafting")
        recipe = Recipe(
            name=raw["name"],
            category=category,
            recipe_type=_recipe_type_from_category(category),
            energy=float(raw.get("energy", 0.5)),
            ingredients=ingredients,
            products=products,
            expansion=raw.get("expansion", "base"),
            label=raw.get("label", raw["name"]),
        )
        recipes[recipe.name] = recipe
        _, role = classify_bundled_recipe(
            recipe.name, recipe.category, recipe.ingredients, recipe.products
        )
        recipe_roles[recipe.name] = role

    return _finalize_database(items, recipes, {}, recipe_roles)


def _recipe_type_from_category(category: str) -> RecipeType:
    from db.intrinsic.constants import CRAFT_CATEGORIES, REFINING_CATEGORIES, SMELTING_CATEGORIES
    if category in SMELTING_CATEGORIES:
        return RecipeType.SMELTING
    if category in REFINING_CATEGORIES:
        return RecipeType.REFINING
    if category == "chemistry":
        return RecipeType.CHEMISTRY
    if category in CRAFT_CATEGORIES:
        return RecipeType.MANUFACTURING
    return RecipeType.MANUFACTURING


def merge_analysis_context(db: RecipeDatabase, ctx) -> RecipeDatabase:
    """将 catalog 上下文合并进 RecipeDatabase（SQLite 路径）。"""
    db.closure_expandable = set(ctx.closure_expandable)
    db.pure_supply = set(ctx.pure_supply)
    return db
