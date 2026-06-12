"""Layer IP — snap_recipe 语义 tag 与 closure_role 分类。"""

from __future__ import annotations

import re
from dataclasses import dataclass

from db.intrinsic.constants import (
    CLOSURE_EXCLUDED,
    CLOSURE_LOGISTICS,
    CLOSURE_PRIMARY,
    CRAFT_CATEGORIES,
    EXTRACT_RECIPE_NAME_HINTS,
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
    flows: list[FlowStack],
) -> tuple[set[str], str]:
    """返回 (ip_tags, closure_role)。"""
    tags: set[str] = set()

    if _FILL_BARREL.match(name):
        tags.add(IP_BARREL_FILL)
    elif _EMPTY_BARREL.match(name):
        tags.add(IP_BARREL_EMPTY)

    if category in SMELTING_CATEGORIES:
        tags.add(IP_SMELTING)
    elif category in REFINING_CATEGORIES:
        if category == "chemistry":
            tags.add(IP_CHEMISTRY)
        else:
            tags.add(IP_REFINING)
    elif category in CRAFT_CATEGORIES and not tags & {IP_BARREL_FILL, IP_BARREL_EMPTY}:
        tags.add(IP_CRAFT)

    if _looks_like_extract(name, category, flows):
        tags.add(IP_EXTRACT)

    if not tags:
        tags.add(IP_CRAFT)

    closure_role = _closure_role_from_tags(tags)
    return tags, closure_role


def _looks_like_extract(name: str, category: str, flows: list[FlowStack]) -> bool:
    if name.startswith("fb-extract:"):
        return True
    if any(h in name for h in EXTRACT_RECIPE_NAME_HINTS):
        return True
    if category in {"mining", "pumping"}:
        return True
    ins = [f for f in flows if f.direction == "in"]
    outs = [f for f in flows if f.direction == "out"]
    if not ins and outs:
        return True
    if ins and all(i.kind == "fluid" and i.name.endswith("-barrel") for i in ins):
        return False
    return False


def _closure_role_from_tags(tags: set[str]) -> str:
    if IP_EXCLUDED in tags:
        return CLOSURE_EXCLUDED
    if tags & {IP_BARREL_FILL, IP_BARREL_EMPTY}:
        return CLOSURE_LOGISTICS
    return CLOSURE_PRIMARY


def classify_bundled_recipe(name: str, category: str, ingredients: list, products: list) -> tuple[set[str], str]:
    flows: list[FlowStack] = []
    for ing in ingredients:
        flows.append(FlowStack(name=ing.name, kind=getattr(ing, "type", "item"), direction="in"))
    for prod in products:
        flows.append(FlowStack(name=prod.name, kind=getattr(prod, "type", "item"), direction="out"))
    return classify_recipe(name=name, category=category, flows=flows)
