"""Layer IP — snap_recipe 语义 tag 与 closure_role 分类。"""

from __future__ import annotations

import re
from dataclasses import dataclass

from db.intrinsic.constants import (
    CLOSURE_EXCLUDED,
    CLOSURE_LOGISTICS,
    CLOSURE_PRIMARY,
    CRAFT_CATEGORIES,
    IP_BARREL_EMPTY,
    IP_BARREL_FILL,
    IP_CHEMISTRY,
    IP_CRAFT,
    IP_EXCLUDED,
    IP_EXTRACT,
    IP_REFINING,
    IP_SMELTING,
    REFINING_CATEGORIES,
    SMELTING_CATEGORIES,
)

_FILL_BARREL = re.compile(r"^fill-.+-barrel$")
_EMPTY_BARREL = re.compile(r"^empty-.+-barrel$")


@dataclass
class FlowStack:
    name: str
    kind: str  # item | fluid
    direction: str  # in | out


def classify_recipe(
    *,
    name: str,
    category: str,
    recipe_type: str,
    flows: list[FlowStack],
) -> tuple[set[str], str]:
    """返回 (ip_tags, closure_role)。"""
    tags: set[str] = set()

    if _FILL_BARREL.match(name):
        tags.add(IP_BARREL_FILL)
    elif _EMPTY_BARREL.match(name):
        tags.add(IP_BARREL_EMPTY)

    if recipe_type == "extraction":
        tags.add(IP_EXTRACT)
    elif recipe_type == "smelting":
        tags.add(IP_SMELTING)
    elif recipe_type == "chemistry":
        tags.add(IP_CHEMISTRY)
    elif recipe_type == "refining":
        tags.add(IP_REFINING)
    elif recipe_type == "manufacturing":
        if category in CRAFT_CATEGORIES and not tags & {IP_BARREL_FILL, IP_BARREL_EMPTY}:
            tags.add(IP_CRAFT)

    if not tags:
        tags.add(IP_CRAFT)

    closure_role = _closure_role_from_tags(tags)
    return tags, closure_role


def _closure_role_from_tags(tags: set[str]) -> str:
    if IP_EXCLUDED in tags:
        return CLOSURE_EXCLUDED
    if tags & {IP_BARREL_FILL, IP_BARREL_EMPTY}:
        return CLOSURE_LOGISTICS
    return CLOSURE_PRIMARY


def classify_bundled_recipe(name: str, category: str, ingredients: list, products: list, recipe_type: str = "manufacturing") -> tuple[set[str], str]:
    flows: list[FlowStack] = []
    for ing in ingredients:
        flows.append(FlowStack(name=ing.name, kind=getattr(ing, "type", "item"), direction="in"))
    for prod in products:
        flows.append(FlowStack(name=prod.name, kind=getattr(prod, "type", "item"), direction="out"))
    return classify_recipe(name=name, category=category, recipe_type=recipe_type, flows=flows)
