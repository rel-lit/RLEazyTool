"""原始树：被降级终端的 layer 语义。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.layout_engine import compute_layout  # noqa: E402
from core.recipe_loader import load_database  # noqa: E402
from models.schemas import LayoutComputeRequest, LayoutOptions, LayoutTarget  # noqa: E402


class DemotedTerminalLayerTest(unittest.TestCase):
    def setUp(self) -> None:
        from db.connection import init_db
        from core.game_session import SESSION

        load_database.cache_clear()
        init_db()
        SESSION.reset()
        self.db = load_database()

    def test_demoted_terminal_expands_instead_of_layer_zero(self) -> None:
        """先建高级电路树时，被降级的电子电路应展开为中间物而非 layer0 叶。"""
        result = compute_layout(
            LayoutComputeRequest(
                targets=[
                    LayoutTarget(item="advanced-circuit"),
                    LayoutTarget(item="electronic-circuit"),
                ],
                layout_options=LayoutOptions(),
            )
        )
        self.assertFalse(result.analysis.get("impossible"))
        self.assertIn("electronic-circuit", result.analysis["demoted_outputs"])
        self.assertIn("advanced-circuit", result.analysis["effective_terminals"])

        ec = next(n for n in result.nodes if n.item == "electronic-circuit")
        ac = next(n for n in result.nodes if n.item == "advanced-circuit")
        self.assertGreater(ec.layer, 0, "被降级终端不应落在 layer0")
        self.assertGreater(ac.layer, ec.layer)
        self.assertEqual(ec.meta.get("node_kind"), "intermediate")
        self.assertEqual(ac.meta.get("node_kind"), "terminal")


if __name__ == "__main__":
    unittest.main()
