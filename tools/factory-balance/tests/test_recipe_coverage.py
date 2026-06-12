"""配方库测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.prototype_loader import build_database_from_dump  # noqa: E402
from core.progress_export import derive_craftable_items  # noqa: E402


class RecipeCoverageTest(unittest.TestCase):
    def test_processing_unit_recipe_in_dump_db(self) -> None:
        dump = Path(__file__).resolve().parent.parent / "backend" / "data" / "cache" / "data-raw-dump.json"
        if not dump.is_file():
            self.skipTest("无本地 data-raw-dump.json")
        db = build_database_from_dump()
        self.assertIn("processing-unit", db.recipes)
        self.assertIn("processing-unit", db.items)

    def test_processing_unit_craftable_when_enabled(self) -> None:
        dump = Path(__file__).resolve().parent.parent / "backend" / "data" / "cache" / "data-raw-dump.json"
        if not dump.is_file():
            self.skipTest("无本地 data-raw-dump.json")
        db = build_database_from_dump()
        craftable = derive_craftable_items(["processing-unit"], db)
        self.assertIn("processing-unit", craftable)


class FilterItemsTest(unittest.TestCase):
    def test_filter_internal_items(self) -> None:
        out = [n for n in ["copper-plate", "parameter-0"] if not n.startswith("parameter-")]
        self.assertEqual(out, ["copper-plate"])


if __name__ == "__main__":
    unittest.main()
