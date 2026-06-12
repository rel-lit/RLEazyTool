"""物品目录与本地化测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.item_catalog import build_item_catalog, is_pure_raw, is_terminal_product  # noqa: E402
from core.prototype_loader import build_database_from_dump  # noqa: E402
from core.recipe_loader import ItemDef  # noqa: E402
from core.progress_export import derive_craftable_items  # noqa: E402


class ItemCatalogTest(unittest.TestCase):
    def test_automation_science_pack_has_chinese_label(self) -> None:
        dump = Path(__file__).resolve().parent.parent / "backend" / "data" / "cache" / "data-raw-dump.json"
        if not dump.is_file():
            self.skipTest("无 dump")
        db = build_database_from_dump()
        item = db.items.get("automation-science-pack")
        self.assertIsNotNone(item)
        assert item is not None
        self.assertNotEqual(item.label, "automation-science-pack")
        self.assertIn("科技包", item.label)

    def test_terminal_excluded_from_supply(self) -> None:
        dump = Path(__file__).resolve().parent.parent / "backend" / "data" / "cache" / "data-raw-dump.json"
        prog = Path.home() / "AppData" / "Roaming" / "Factorio" / "script-output" / "factory-balance-progress.json"
        if not dump.is_file() or not prog.is_file():
            self.skipTest("无 dump/进度")
        import json

        enabled = json.loads(prog.read_text(encoding="utf-8"))["enabled_recipes"]
        db = build_database_from_dump(enabled_recipes=set(enabled))
        craftable = set(derive_craftable_items(enabled, build_database_from_dump()))
        catalog = build_item_catalog(db, craftable)
        supply_names = {i.name for i in catalog.supply_items}
        manufacture_names = {i.name for i in catalog.manufacture_items}
        self.assertIn("processing-unit", manufacture_names)
        self.assertIn("copper-plate", supply_names)
        self.assertNotIn("copper-ore", manufacture_names)

    def test_pure_raw_helpers(self) -> None:
        ore = ItemDef(name="iron-ore", label="铁矿", is_raw=True)
        plate = ItemDef(name="iron-plate", label="铁板", is_raw=False)
        craftable = {"iron-plate"}
        self.assertTrue(is_pure_raw("iron-ore", ore, craftable))
        self.assertFalse(is_pure_raw("iron-plate", plate, craftable))
        self.assertTrue(is_terminal_product("satellite", {"processing-unit"}))


if __name__ == "__main__":
    unittest.main()
