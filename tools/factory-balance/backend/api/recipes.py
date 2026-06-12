from __future__ import annotations

from fastapi import APIRouter, Query

from core.game_session import SESSION
from models.schemas import ItemCatalogResponse, ItemInfo, RecipeInfo, RecipeSearchResponse

router = APIRouter(tags=["recipes"])


def _item_info(i) -> ItemInfo:
    return ItemInfo(
        name=i.name,
        label=i.label,
        group=i.group,
        is_raw=i.is_raw,
        expansion=i.expansion,
    )


@router.get("/recipes/search", response_model=RecipeSearchResponse)
def search_recipes(
    q: str = Query("", description="搜索关键词"),
    craftable_only: bool = Query(False, description="仅显示当前存档可制造产物"),
) -> RecipeSearchResponse:
    db = SESSION.get_active_database()
    if craftable_only and SESSION.craftable_items:
        items = SESSION.get_item_catalog().manufacture_items
        if q.strip():
            ql = q.strip().lower()
            items = [i for i in items if ql in i.label.lower() or ql in i.name.lower()]
    else:
        items, _ = db.search(q, expansion="all")

    _, recipes = db.search(q, expansion="all")
    return RecipeSearchResponse(
        items=[_item_info(i) for i in items],
        recipes=[
            RecipeInfo(
                name=r.name,
                label=r.label,
                category=r.category,
                energy=r.energy,
                products=[{"name": p.name, "amount": p.amount, "type": p.type} for p in r.products],
                ingredients=[
                    {"name": ing.name, "amount": ing.amount, "type": ing.type} for ing in r.ingredients
                ],
                expansion=r.expansion,
            )
            for r in recipes
        ],
        filtered_by_progress=bool(SESSION.craftable_items and craftable_only),
        database_source=SESSION.database_source,
    )


@router.get("/items/{name}/producers")
def item_producers(name: str) -> dict:
    db = SESSION.get_active_database()
    recipe = db.default_recipe_for(name, SESSION.enabled_recipes or None)
    if not recipe:
        return {"item": name, "recipe": None}
    return {
        "item": name,
        "recipe": recipe.name,
        "ingredients": [{"name": i.name, "amount": i.amount} for i in recipe.ingredients],
    }
