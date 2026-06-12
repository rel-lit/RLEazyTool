"""终态 schema 集成测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

import db.connection as conn_mod  # noqa: E402
from db.app_state import purge_stale, set_active_save_key  # noqa: E402
from db.catalog_builder import build_catalog  # noqa: E402
from db.catalog_query import query_catalog  # noqa: E402
from db.connection import init_db  # noqa: E402
from db.environment_store import register_environment  # noqa: E402
from db.recipe_loader_db import load_recipe_database  # noqa: E402
from db.save_store import get_enabled_recipe_names, upsert_save_progress  # noqa: E402
from db.snapshot_etl import ingest_dump_file  # noqa: E402


MINI_DUMP = {
    "item": {
        "copper-plate": {"type": "item", "subgroup": "raw-material"},
        "electronic-circuit": {"type": "item", "subgroup": "intermediate-product"},
        "advanced-circuit": {"type": "item", "subgroup": "intermediate-product"},
        "copper-cable": {"type": "item", "subgroup": "intermediate-product"},
    },
    "fluid": {},
    "recipe": {
        "copper-cable": {
            "type": "recipe",
            "category": "crafting",
            "energy": 0.5,
            "ingredients": [{"type": "item", "name": "copper-plate", "amount": 1}],
            "results": [{"type": "item", "name": "copper-cable", "amount": 2}],
        },
        "electronic-circuit": {
            "type": "recipe",
            "category": "crafting",
            "energy": 0.5,
            "ingredients": [{"type": "item", "name": "copper-cable", "amount": 3}],
            "results": [{"type": "item", "name": "electronic-circuit", "amount": 1}],
        },
        "advanced-circuit": {
            "type": "recipe",
            "category": "crafting",
            "energy": 6,
            "ingredients": [{"type": "item", "name": "electronic-circuit", "amount": 2}],
            "results": [{"type": "item", "name": "advanced-circuit", "amount": 1}],
        },
    },
}


class FinalSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        conn_mod.DB_PATH = Path(self._tmpdir.name) / "test.db"
        init_db(reset=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _ingest_mini(self) -> tuple[int, str]:
        import json

        dump = Path(self._tmpdir.name) / "mini.json"
        dump.write_text(json.dumps(MINI_DUMP), encoding="utf-8")
        snapshot_id, sha = ingest_dump_file(dump, locale="zh-CN", mod_names=["base"])
        env_key = register_environment(
            snapshot_id=snapshot_id,
            factorio_version="2.0.76",
            mod_fingerprint="testfp1234567890",
            locale="zh-CN",
            mods=[("base", "2.0.76")],
        )
        build_catalog(scope_kind="environment", scope_key=env_key, env_key=env_key)
        return snapshot_id, env_key

    def test_save_gate_and_catalog_tags(self) -> None:
        snapshot_id, env_key = self._ingest_mini()
        save_path = Path(self._tmpdir.name) / "test.zip"
        save_path.write_bytes(b"x")
        upsert_save_progress(
            save_key="test-save",
            save_path=save_path,
            env_key=env_key,
            enabled_recipe_names=["advanced-circuit", "electronic-circuit", "copper-cable"],
            researched_tech_names=[],
            exported_tick=1,
            snapshot_id=snapshot_id,
        )
        enabled = get_enabled_recipe_names("test-save")
        self.assertIn("advanced-circuit", enabled)

        cat = query_catalog(scope_kind="save", scope_key="test-save")
        mfg = {i.name for i in cat.manufacture_items}
        self.assertIn("advanced-circuit", mfg)

        db = load_recipe_database(env_key, save_key="test-save")
        self.assertIn("advanced-circuit", db.recipes)
        self.assertNotIn("quantum-processor", db.recipes)

    def test_purge_keeps_active_save(self) -> None:
        snapshot_id, env_key = self._ingest_mini()
        save_a = Path(self._tmpdir.name) / "a.zip"
        save_b = Path(self._tmpdir.name) / "b.zip"
        save_a.write_bytes(b"a")
        save_b.write_bytes(b"b")
        upsert_save_progress(
            save_key="save-a",
            save_path=save_a,
            env_key=env_key,
            enabled_recipe_names=["copper-cable"],
            researched_tech_names=[],
            exported_tick=1,
            snapshot_id=snapshot_id,
        )
        upsert_save_progress(
            save_key="save-b",
            save_path=save_b,
            env_key=env_key,
            enabled_recipe_names=["electronic-circuit"],
            researched_tech_names=[],
            exported_tick=2,
            snapshot_id=snapshot_id,
        )
        set_active_save_key("save-a")
        result = purge_stale(keep_active=True)
        self.assertEqual(result["deleted_saves"], 1)
        self.assertTrue(get_enabled_recipe_names("save-a"))


if __name__ == "__main__":
    unittest.main()
