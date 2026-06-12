"""SBTO 与布局引擎单元测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.graph_builder import build_graph  # noqa: E402
from core.layout_engine import compute_layout  # noqa: E402
from core.recipe_loader import load_database  # noqa: E402
from core.sbto import compute_all_tap_orders  # noqa: E402
from models.schemas import LayoutComputeRequest, LayoutTarget, SupplyMode  # noqa: E402


class SbtoCircuitChainTest(unittest.TestCase):
    def setUp(self) -> None:
        from db.connection import init_db
        from core.game_session import SESSION

        init_db()
        SESSION.reset()
        self.db = load_database()
        self.abundant = {
            "iron-plate",
            "plastic-bar",
            "sulfuric-acid",
            "copper-plate",
        }

    def _graph_for(self, target: str):
        return build_graph(
            target_items=[target],
            supplied_items=set(),
            abundant_items=self.abundant,
            db=self.db,
        )

    def test_copper_cable_red_before_green(self) -> None:
        graph = self._graph_for("processing-unit")
        taps = compute_all_tap_orders(graph, ["processing-unit"], {k: v.label for k, v in self.db.items.items()})
        cable = next(t for t in taps if t.item == "copper-cable")
        red_id = "producer:advanced-circuit"
        green_id = "producer:electronic-circuit"
        self.assertLess(cable.order.index(red_id), cable.order.index(green_id))

    def test_green_circuit_blue_before_red(self) -> None:
        graph = self._graph_for("processing-unit")
        taps = compute_all_tap_orders(graph, ["processing-unit"], {k: v.label for k, v in self.db.items.items()})
        green = next(t for t in taps if t.item == "electronic-circuit")
        blue_id = "producer:processing-unit"
        red_id = "producer:advanced-circuit"
        self.assertLess(green.order.index(blue_id), green.order.index(red_id))

    def test_quantum_processor_chain(self) -> None:
        req = LayoutComputeRequest(
            targets=[LayoutTarget(item="quantum-processor")],
            supply_mode=SupplyMode.RAW,
            supplied_items=["copper-plate"],
        )
        result = compute_layout(req)
        self.assertGreater(len(result.nodes), 4)
        self.assertTrue(any(t.item == "copper-cable" for t in result.tap_orders))

    def test_direct_supply_skips_green_producer(self) -> None:
        req = LayoutComputeRequest(
            targets=[LayoutTarget(item="advanced-circuit")],
            supply_mode=SupplyMode.DIRECT,
            supplied_items=["electronic-circuit", "copper-plate"],
        )
        result = compute_layout(req)
        node_ids = {n.id for n in result.nodes}
        self.assertNotIn("producer:electronic-circuit", node_ids)
        self.assertTrue(any("直接产物模式" in w for w in result.warnings))


if __name__ == "__main__":
    unittest.main()
