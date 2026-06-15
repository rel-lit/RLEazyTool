"""recipe_display 单元测试。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.recipe_display import build_recipe_details, format_recipe_line  # noqa: E402
from core.recipe_loader import ItemDef, ItemStack, Recipe, RecipeDatabase  # noqa: E402
from db.intrinsic.constants import IR_EXTRACTABLE  # noqa: E402


class RecipeDisplayTests(unittest.TestCase):
    def test_format_recipe_line(self) -> None:
        db = RecipeDatabase(
            items={
                "iron-plate": ItemDef("iron-plate", "铁板"),
                "iron-gear-wheel": ItemDef("iron-gear-wheel", "铁齿轮"),
            },
            recipes={
                "igw": Recipe(
                    name="igw",
                    category="crafting",
                    energy=0.5,
                    ingredients=[ItemStack("iron-plate", 2)],
                    products=[ItemStack("iron-gear-wheel", 1)],
                    label="铁齿轮",
                )
            },
        )
        line = format_recipe_line(db.recipes["igw"], {"iron-plate": "铁板", "iron-gear-wheel": "铁齿轮"})
        self.assertEqual(line, "铁板×2 → 铁齿轮×1")

    def test_build_recipe_details_world_supply(self) -> None:
        db = RecipeDatabase(
            items={
                "iron-ore": ItemDef("iron-ore", "铁矿"),
                "iron-plate": ItemDef("iron-plate", "铁板"),
            },
            recipes={
                "ip": Recipe(
                    name="ip",
                    category="crafting",
                    energy=0.5,
                    ingredients=[ItemStack("iron-ore", 1)],
                    products=[ItemStack("iron-plate", 1)],
                    label="铁板",
                )
            },
            resource_intrinsic_tags={"iron-ore": {IR_EXTRACTABLE}},
            pure_supply={"iron-ore"},
        )
        details = build_recipe_details(
            {"iron-plate": "ip"},
            db,
            analysis_items={"iron-plate", "iron-ore"},
        )
        self.assertEqual(details["iron-ore"]["kind"], "world-supply")
        self.assertIn("世界开采", details["iron-ore"]["line"])
        self.assertIn("铁矿", details["iron-ore"]["line"])

    def test_build_recipe_details_extract(self) -> None:
        db = RecipeDatabase(items={"crude-oil": ItemDef("crude-oil", "原油")}, recipes={})
        details = build_recipe_details({"crude-oil": "fb-extract:crude-oil"}, db)
        self.assertEqual(details["crude-oil"]["kind"], "extract")
        self.assertIn("世界抽取", details["crude-oil"]["line"])


if __name__ == "__main__":
    unittest.main()
