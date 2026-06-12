"""Intrinsic tag 与闭包分析测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.analysis_engine import run_analysis  # noqa: E402
from core.recipe_loader import ItemDef, ItemStack, Recipe, RecipeDatabase, _finalize_database  # noqa: E402
from db.intrinsic.constants import IR_EXTRACTABLE  # noqa: E402
from db.intrinsic.recipe_classifier import classify_recipe, FlowStack  # noqa: E402
from db.intrinsic.resource_classifier import classify_resource  # noqa: E402
from models.schemas import SupplyMode  # noqa: E402


class IntrinsicClassifierTest(unittest.TestCase):
    def test_water_is_extractable(self) -> None:
        tags, _, is_raw = classify_resource(
            name="water",
            kind="fluid",
            visibility="normal",
            item_subgroup=None,
            world_extractable={("fluid", "water")},
        )
        self.assertIn("ir.extractable", tags)
        self.assertTrue(is_raw)

    def test_petroleum_gas_not_extractable(self) -> None:
        tags, _, is_raw = classify_resource(
            name="petroleum-gas", kind="fluid", visibility="normal", item_subgroup=None
        )
        self.assertNotIn(IR_EXTRACTABLE, tags)
        self.assertFalse(is_raw)

    def test_crude_oil_is_extractable(self) -> None:
        tags, _, is_raw = classify_resource(
            name="crude-oil",
            kind="fluid",
            visibility="normal",
            item_subgroup=None,
            world_extractable={("fluid", "crude-oil")},
        )
        self.assertIn(IR_EXTRACTABLE, tags)
        self.assertTrue(is_raw)

    def test_water_barrel_is_container(self) -> None:
        tags, params, _ = classify_resource(
            name="water-barrel", kind="item", visibility="normal", item_subgroup=None
        )
        self.assertIn("ir.container.barrel", tags)
        self.assertEqual(params["content_fluid"], "water")

    def test_empty_water_barrel_is_logistics(self) -> None:
        flows = [
            FlowStack("water-barrel", "item", "in"),
            FlowStack("water", "fluid", "out"),
            FlowStack("empty-barrel", "item", "out"),
        ]
        tags, role = classify_recipe(name="empty-water-barrel", category="crafting-with-fluid", flows=flows)
        self.assertIn("ip.barrel.empty", tags)
        self.assertEqual(role, "logistics")


class WaterClosureTest(unittest.TestCase):
    def _mini_db(self, *, include_pump: bool = False) -> RecipeDatabase:
        items = {
            "water": ItemDef("water", "水", kind="fluid"),
            "water-barrel": ItemDef("water-barrel", "水桶", kind="item"),
            "empty-barrel": ItemDef("empty-barrel", "空桶", kind="item"),
            "electronic-circuit": ItemDef("electronic-circuit", "绿板", kind="item"),
            "copper-cable": ItemDef("copper-cable", "铜线", kind="item"),
            "copper-plate": ItemDef("copper-plate", "铜板", kind="item"),
        }
        recipes: dict[str, Recipe] = {}
        if include_pump:
            recipes["offshore-pump-water"] = Recipe(
                name="offshore-pump-water",
                category="pumping",
                energy=1,
                ingredients=[],
                products=[ItemStack("water", 1200, "fluid")],
            )
        recipes.update(
            {
                "empty-water-barrel": Recipe(
                    name="empty-water-barrel",
                    category="crafting-with-fluid",
                    energy=0.2,
                    ingredients=[ItemStack("water-barrel", 1, "item")],
                    products=[
                        ItemStack("water", 50, "fluid"),
                        ItemStack("empty-barrel", 1, "item"),
                    ],
                ),
                "fill-water-barrel": Recipe(
                    name="fill-water-barrel",
                    category="crafting-with-fluid",
                    energy=0.2,
                    ingredients=[
                        ItemStack("empty-barrel", 1, "item"),
                        ItemStack("water", 50, "fluid"),
                    ],
                    products=[ItemStack("water-barrel", 1, "item")],
                ),
                "copper-cable": Recipe(
                    name="copper-cable",
                    category="crafting",
                    energy=0.5,
                    ingredients=[ItemStack("copper-plate", 1, "item")],
                    products=[ItemStack("copper-cable", 2, "item")],
                ),
                "electronic-circuit": Recipe(
                    name="electronic-circuit",
                    category="crafting",
                    energy=0.5,
                    ingredients=[
                        ItemStack("copper-cable", 3, "item"),
                        ItemStack("water", 5, "fluid"),
                    ],
                    products=[ItemStack("electronic-circuit", 1, "item")],
                ),
            }
        )
        roles = {}
        for name, recipe in recipes.items():
            flows = []
            for ing in recipe.ingredients:
                flows.append(FlowStack(ing.name, ing.type, "in"))
            for prod in recipe.products:
                flows.append(FlowStack(prod.name, prod.type, "out"))
            _, roles[name] = classify_recipe(name=name, category=recipe.category, flows=flows)

        db = _finalize_database(items, recipes, {}, roles)
        return db

    def test_only_barrel_recipes_water_is_supply(self) -> None:
        db = self._mini_db()
        d = set(db.items.keys())
        result = run_analysis(
            declared_outputs=["electronic-circuit"],
            supply_mode=SupplyMode.RAW,
            user_supplied=[],
            forbidden=[],
            db=db,
            data_source=d,
            closure_expandable={"electronic-circuit", "copper-cable"},
            pure_supply={"water"},
        )
        self.assertFalse(result.summary.impossible)
        self.assertIn("water", result.summary.true_pure_sources)
        self.assertNotIn("water-barrel", result.summary.analysis_items)

    def test_pump_unlocked_water_is_producer(self) -> None:
        db = self._mini_db(include_pump=True)
        d = set(db.items.keys())
        expandable = {"electronic-circuit", "copper-cable", "water"}
        result = run_analysis(
            declared_outputs=["electronic-circuit"],
            supply_mode=SupplyMode.RAW,
            user_supplied=[],
            forbidden=[],
            db=db,
            data_source=d,
            closure_expandable=expandable,
            pure_supply=set(),
        )
        self.assertFalse(result.summary.impossible)
        self.assertIn("producer:offshore-pump-water", set(result.graph.producers.keys()))
        self.assertNotIn("water", result.summary.true_pure_sources)


class PetroleumGasClosureTest(unittest.TestCase):
    def _oil_db(self) -> RecipeDatabase:
        items = {
            "crude-oil": ItemDef("crude-oil", "原油", kind="fluid"),
            "petroleum-gas": ItemDef("petroleum-gas", "石油气", kind="fluid"),
            "coal": ItemDef("coal", "煤", kind="item"),
            "plastic-bar": ItemDef("plastic-bar", "塑料", kind="item"),
        }
        recipes = {
            "pumpjack-crude-oil": Recipe(
                name="pumpjack-crude-oil",
                category="pumping",
                energy=1,
                ingredients=[],
                products=[ItemStack("crude-oil", 100, "fluid")],
            ),
            "basic-oil-processing": Recipe(
                name="basic-oil-processing",
                category="oil-processing",
                energy=5,
                ingredients=[ItemStack("crude-oil", 100, "fluid")],
                products=[
                    ItemStack("petroleum-gas", 50, "fluid"),
                    ItemStack("heavy-oil", 30, "fluid"),
                    ItemStack("light-oil", 20, "fluid"),
                ],
            ),
            "plastic-bar": Recipe(
                name="plastic-bar",
                category="chemistry",
                energy=1,
                ingredients=[
                    ItemStack("petroleum-gas", 20, "fluid"),
                    ItemStack("coal", 1, "item"),
                ],
                products=[ItemStack("plastic-bar", 2, "item")],
            ),
        }
        roles = {}
        for name, recipe in recipes.items():
            flows = []
            for ing in recipe.ingredients:
                flows.append(FlowStack(ing.name, ing.type, "in"))
            for prod in recipe.products:
                flows.append(FlowStack(prod.name, prod.type, "out"))
            _, roles[name] = classify_recipe(name=name, category=recipe.category, flows=flows)

        return _finalize_database(items, recipes, {}, roles)

    def test_petroleum_gas_expands_from_crude_oil(self) -> None:
        db = self._oil_db()
        d = set(db.items.keys())
        expandable = {"plastic-bar", "petroleum-gas", "crude-oil"}
        result = run_analysis(
            declared_outputs=["plastic-bar"],
            supply_mode=SupplyMode.RAW,
            user_supplied=[],
            forbidden=[],
            db=db,
            data_source=d,
            closure_expandable=expandable,
            pure_supply=set(),
        )
        self.assertFalse(result.summary.impossible)
        self.assertIn("producer:basic-oil-processing", set(result.graph.producers.keys()))
        self.assertIn("producer:pumpjack-crude-oil", set(result.graph.producers.keys()))
        self.assertNotIn("petroleum-gas", result.summary.true_pure_sources)
        self.assertNotIn("crude-oil", result.summary.true_pure_sources)


if __name__ == "__main__":
    unittest.main()
