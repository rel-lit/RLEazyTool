"""v2 流水线集成测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.layout_engine import compute_layout  # noqa: E402
from core.layout_pipeline import run_layout_pipeline  # noqa: E402
from core.recipe_loader import load_database  # noqa: E402
from models.schemas import (  # noqa: E402
    LayoutComputeRequest,
    LayoutOptions,
    LayoutTarget,
    SupplyMode,
)


class PipelineIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        from db.connection import init_db
        from core.game_session import SESSION

        load_database.cache_clear()
        init_db()
        SESSION.reset()
        self.db = load_database()

    def _req(self, target: str, **kwargs) -> LayoutComputeRequest:
        return LayoutComputeRequest(
            targets=[LayoutTarget(item=target)],
            supply_mode=kwargs.get("supply_mode", SupplyMode.RAW),
            supplied_items=kwargs.get("supplied_items", []),
            forbidden_items=kwargs.get("forbidden_items", []),
            layout_options=LayoutOptions(),
        )

    def test_processing_unit_sbto_chains(self) -> None:
        result = compute_layout(self._req("processing-unit"))
        self.assertFalse(result.analysis.get("impossible"))
        self.assertGreater(len(result.nodes), 4)
        self.assertTrue(any(e.type == "tap_chain" for e in result.edges))
        cable = next(t for t in result.tap_orders if t.item == "copper-cable")
        self.assertLess(
            cable.order.index("advanced-circuit"),
            cable.order.index("electronic-circuit"),
        )
        green = next(t for t in result.tap_orders if t.item == "electronic-circuit")
        self.assertLess(
            green.order.index("processing-unit"),
            green.order.index("advanced-circuit"),
        )

    def test_copper_cable_hidden_fanout(self) -> None:
        result = compute_layout(self._req("processing-unit"))
        self.assertGreater(len(result.hidden_edges), 0)
        self.assertTrue(all(e.type == "hidden" for e in result.hidden_edges))

    def test_quantum_processor_chain(self) -> None:
        result = compute_layout(
            self._req("quantum-processor", supplied_items=["copper-plate"])
        )
        self.assertTrue(any(e.type == "tap_chain" for e in result.edges))

    def test_direct_supply_skips_green_producer(self) -> None:
        result = compute_layout(
            LayoutComputeRequest(
                targets=[LayoutTarget(item="advanced-circuit")],
                supply_mode=SupplyMode.DIRECT,
                supplied_items=["electronic-circuit", "copper-plate"],
                layout_options=LayoutOptions(),
            )
        )
        ec = next(n for n in result.nodes if n.item == "electronic-circuit")
        self.assertTrue(ec.meta.get("external_leaf"))
        self.assertNotIn("electronic-circuit", ec.meta.get("recipe", ""))
        self.assertIn("plastic-bar", result.analysis.get("pseudo_external", []))

    def test_forbidden_blocks_when_tree_unbuildable(self) -> None:
        result = run_layout_pipeline(
            self._req("electronic-circuit", forbidden_items=["copper-plate"]),
            self.db,
        )
        self.assertTrue(result.analysis.get("impossible"))
        self.assertEqual(len(result.nodes), 0)

    def test_nodes_use_item_ids(self) -> None:
        result = compute_layout(self._req("electronic-circuit"))
        for n in result.nodes:
            self.assertEqual(n.id, n.item)
            self.assertEqual(n.type, "item")

    def test_node_kind_meta_and_max_layer(self) -> None:
        result = compute_layout(self._req("processing-unit"))
        self.assertIn("max_layer", result.analysis)
        self.assertGreater(result.analysis["max_layer"], 0)
        terminal = next(n for n in result.nodes if n.item == "processing-unit")
        self.assertEqual(terminal.meta.get("node_kind"), "terminal")
        pure = [n for n in result.nodes if n.meta.get("node_kind") == "pure_source"]
        self.assertTrue(pure)
        circuit = next(n for n in result.nodes if n.item == "electronic-circuit")
        self.assertEqual(circuit.meta.get("node_kind"), "intermediate")

    def test_demoted_outputs_when_terminal_absorbed(self) -> None:
        result = compute_layout(
            LayoutComputeRequest(
                targets=[
                    LayoutTarget(item="advanced-circuit"),
                    LayoutTarget(item="electronic-circuit"),
                ],
                layout_options=LayoutOptions(),
            )
        )
        analysis = result.analysis
        self.assertFalse(analysis.get("impossible"))
        self.assertIn("advanced-circuit", analysis["declared_outputs"])
        self.assertIn("advanced-circuit", analysis["effective_terminals"])
        self.assertIn("electronic-circuit", analysis["demoted_outputs"])
        self.assertNotIn("electronic-circuit", analysis["effective_terminals"])
        self.assertIn("electronic-circuit", analysis["analysis_items"])


if __name__ == "__main__":
    unittest.main()
