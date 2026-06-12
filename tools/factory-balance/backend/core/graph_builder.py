"""从产出目标反向展开生产图。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .recipe_loader import ItemDef, Recipe, RecipeDatabase, load_database


@dataclass
class ProductionNode:
    id: str
    recipe_name: str
    product: str
    label: str
    inputs: list[str]
    outputs: list[str]
    layer_hint: int = 0


@dataclass
class SupplyNode:
    id: str
    item: str
    label: str


@dataclass
class ProductionGraph:
    producers: dict[str, ProductionNode] = field(default_factory=dict)
    supplies: dict[str, SupplyNode] = field(default_factory=dict)
    sinks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def consumers_of(self, item: str) -> list[ProductionNode]:
        return [n for n in self.producers.values() if item in n.inputs]

    def producer_of(self, item: str) -> ProductionNode | None:
        for node in self.producers.values():
            if item in node.outputs:
                return node
        return None


def _node_id(recipe_name: str) -> str:
    return f"producer:{recipe_name}"


def _supply_id(item: str) -> str:
    return f"supply:{item}"


def build_graph(
    target_items: list[str],
    supplied_items: set[str],
    abundant_items: set[str],
    db: RecipeDatabase | None = None,
    allowed_recipes: set[str] | None = None,
) -> ProductionGraph:
    db = db or load_database()
    graph = ProductionGraph()
    needed: set[str] = set()
    queue: list[str] = list(target_items)

    for item in target_items:
        if item not in db.items and db.default_recipe_for(item) is None:
            graph.warnings.append(f"未知产出物: {item}")

    while queue:
        item = queue.pop(0)
        if item in needed:
            continue
        needed.add(item)

        if item in supplied_items or item in abundant_items:
            graph.supplies[item] = SupplyNode(
                id=_supply_id(item),
                item=item,
                label=db.items[item].label if item in db.items else item,
            )
            continue

        recipe = db.default_recipe_for(item, allowed_recipes)
        if recipe is None:
            graph.warnings.append(f"缺少配方且未标记供给: {item}")
            graph.supplies[item] = SupplyNode(
                id=_supply_id(item),
                item=item,
                label=db.items[item].label if item in db.items else item,
            )
            continue

        node = _recipe_to_node(recipe, db)
        graph.producers[node.id] = node

        for ing in recipe.ingredients:
            if ing.type != "item":
                if ing.name not in abundant_items and ing.name not in supplied_items:
                    graph.warnings.append(
                        f"流体 {ing.name} 未标记为充足或供给，已视为外部供给"
                    )
                    graph.supplies[ing.name] = SupplyNode(
                        id=_supply_id(ing.name),
                        item=ing.name,
                        label=ing.name,
                    )
                continue
            if ing.name not in needed:
                queue.append(ing.name)

    for item in target_items:
        graph.sinks.append(item)

    return graph


def _recipe_to_node(recipe: Recipe, db: RecipeDatabase) -> ProductionNode:
    main_product = recipe.products[0].name if recipe.products else recipe.name
    return ProductionNode(
        id=_node_id(recipe.name),
        recipe_name=recipe.name,
        product=main_product,
        label=(
            db.items[main_product].label
            if main_product in db.items
            else recipe.label
        ),
        inputs=[i.name for i in recipe.ingredients if i.type == "item"],
        outputs=[p.name for p in recipe.products if p.type == "item"],
    )