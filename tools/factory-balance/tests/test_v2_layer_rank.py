"""v2 layer / rank 单元测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.original_graph import OriginalGraph  # noqa: E402
from core.rank_assigner import assign_ranks  # noqa: E402
from core.tree_layer import finalize_layers  # noqa: E402


class V2LayerRankTest(unittest.TestCase):
    def test_linear_chain_layers(self) -> None:
        g = OriginalGraph()
        g.add_dependency("a", "b")
        g.add_dependency("b", "c")
        g.nodes["a"].is_external_leaf = True
        finalize_layers(g)
        self.assertEqual(g.nodes["a"].layer, 0)
        self.assertEqual(g.nodes["b"].layer, 1)
        self.assertEqual(g.nodes["c"].layer, 2)

    def test_rank_monotonic_within_layer(self) -> None:
        g = OriginalGraph()
        g.add_dependency("x", "p")
        g.add_dependency("y", "p")
        g.nodes["x"].is_external_leaf = True
        g.nodes["y"].is_external_leaf = True
        finalize_layers(g)
        assign_ranks(g)
        self.assertNotEqual(g.nodes["x"].rank, g.nodes["y"].rank)

    def test_merge_takes_max_layer(self) -> None:
        g = OriginalGraph()
        g.add_dependency("leaf", "mid")
        g.nodes["leaf"].is_external_leaf = True
        finalize_layers(g)
        other = OriginalGraph()
        other.add_dependency("leaf", "top")
        other.nodes["leaf"].layer = 0
        other.nodes["top"].layer = 5
        g.merge_from(other)
        finalize_layers(g)
        self.assertGreaterEqual(g.nodes["top"].layer, g.nodes["mid"].layer)


if __name__ == "__main__":
    unittest.main()
