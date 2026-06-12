"""分析引擎单元测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.analysis_engine import (  # noqa: E402
    build_production_graph,
    compute_effective_terminals,
    run_analysis,
)
from core.recipe_loader import load_database  # noqa: E402
from models.schemas import SupplyMode  # noqa: E402


class AnalysisEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        from db.connection import init_db
        from core.game_session import SESSION

        init_db()
        SESSION.reset()
        self.db = load_database()
        self.d = set(self.db.items.keys())
        self.craftable = set(self.db.recipes_by_product.keys()) & self.d

    def test_direct_mode_treats_missing_as_pseudo_pure(self) -> None:
        result = run_analysis(
            declared_outputs=["advanced-circuit"],
            supply_mode=SupplyMode.DIRECT,
            user_supplied=["electronic-circuit", "copper-plate"],
            forbidden=[],
            db=self.db,
            data_source=self.d,
            craftable_in_d=self.craftable,
        )
        self.assertFalse(result.summary.impossible)
        node_ids = set(result.graph.producers.keys())
        self.assertNotIn("producer:electronic-circuit", node_ids)
        self.assertIn("plastic-bar", result.summary.pseudo_pure_sources)

    def test_raw_mode_expands_to_non_manufacturable(self) -> None:
        result = run_analysis(
            declared_outputs=["electronic-circuit"],
            supply_mode=SupplyMode.RAW,
            user_supplied=[],
            forbidden=[],
            db=self.db,
            data_source=self.d,
            craftable_in_d=self.craftable,
        )
        self.assertFalse(result.summary.impossible)
        # bundled 数据无冶炼配方，铜板/铁板在 D 内不可制造 → 真纯粹源
        self.assertIn("copper-plate", result.summary.true_pure_sources)
        self.assertIn("iron-plate", result.summary.true_pure_sources)

    def test_demote_green_when_red_also_selected(self) -> None:
        pick = {
            p: self.db.recipes_by_product[p][0]
            for p in self.craftable
            if self.db.recipes_by_product.get(p)
        }
        effective, demoted = compute_effective_terminals(
            ["advanced-circuit", "electronic-circuit"],
            pick,
            self.db,
        )
        self.assertIn("advanced-circuit", effective)
        self.assertIn("electronic-circuit", demoted)

    def test_forbidden_blocks_analysis(self) -> None:
        result = run_analysis(
            declared_outputs=["electronic-circuit"],
            supply_mode=SupplyMode.RAW,
            user_supplied=[],
            forbidden=["copper-plate"],
            db=self.db,
            data_source=self.d,
            craftable_in_d=self.craftable,
        )
        self.assertTrue(result.summary.impossible)
        self.assertTrue(any("已禁止" in w for w in result.warnings))


if __name__ == "__main__":
    unittest.main()
