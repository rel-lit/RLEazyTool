"""布局分层与存档过期检测测试。"""

from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.graph_builder import ProductionGraph, ProductionNode, SupplyNode, _node_id, _supply_id  # noqa: E402
from core.layout_engine import _assign_layers  # noqa: E402
from db.connection import get_connection, init_db  # noqa: E402
from db.save_store import (  # noqa: E402
    get_save_progress_state,
    has_save_progress,
    is_save_progress_stale,
    upsert_save_progress,
)


class AssignLayersTest(unittest.TestCase):
    def test_cycle_does_not_hang(self) -> None:
        graph = ProductionGraph()
        graph.supplies["iron-ore"] = SupplyNode(
            id=_supply_id("iron-ore"), item="iron-ore", label="铁矿"
        )
        a = ProductionNode(
            id=_node_id("recipe-a"),
            recipe_name="recipe-a",
            product="item-a",
            label="A",
            inputs=["item-b"],
            outputs=["item-a"],
        )
        b = ProductionNode(
            id=_node_id("recipe-b"),
            recipe_name="recipe-b",
            product="item-b",
            label="B",
            inputs=["item-a"],
            outputs=["item-b"],
        )
        graph.producers[a.id] = a
        graph.producers[b.id] = b

        layers, warnings = _assign_layers(graph, ["item-a"])
        self.assertGreaterEqual(len(layers), 3)
        self.assertIn(_node_id("recipe-a"), layers)
        self.assertIn(_node_id("recipe-b"), layers)


class SaveStalenessTest(unittest.TestCase):
    def setUp(self) -> None:
        import json

        import db.connection as conn_mod

        self._tmpdir = tempfile.TemporaryDirectory()
        conn_mod.DB_PATH = Path(self._tmpdir.name) / "test.db"
        init_db(reset=True)

        dump = Path(self._tmpdir.name) / "mini.json"
        dump.write_text(json.dumps({"item": {}, "fluid": {}, "recipe": {}}), encoding="utf-8")
        from db.snapshot_etl import ingest_dump_file
        from db.environment_store import register_environment

        snapshot_id, _ = ingest_dump_file(dump, locale="zh-CN", mod_names=["base"])
        self.env_key = register_environment(
            snapshot_id=snapshot_id,
            factorio_version="2.0.76",
            mod_fingerprint="testfp1234567890",
            locale="zh-CN",
            mods=[("base", "2.0.76")],
        )

        self.tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        self.tmp.write(b"save")
        self.tmp.close()
        self.save_path = Path(self.tmp.name)
        self.save_key = "test-save"

    def tearDown(self) -> None:
        self.save_path.unlink(missing_ok=True)
        self._tmpdir.cleanup()

    def test_stale_after_mtime_changes(self) -> None:
        upsert_save_progress(
            save_key=self.save_key,
            save_path=self.save_path,
            env_key=self.env_key,
            enabled_recipe_names=[],
            researched_tech_names=[],
            exported_tick=1,
            snapshot_id=1,
        )
        self.assertTrue(has_save_progress(self.save_key))
        self.assertFalse(is_save_progress_stale(self.save_key, self.save_path))

        time.sleep(1.2)
        self.save_path.write_bytes(b"save-updated")

        self.assertTrue(is_save_progress_stale(self.save_key, self.save_path))
        state = get_save_progress_state(self.save_key, self.save_path)
        self.assertTrue(state["has_cached_progress"])
        self.assertTrue(state["needs_reimport"])


if __name__ == "__main__":
    unittest.main()
