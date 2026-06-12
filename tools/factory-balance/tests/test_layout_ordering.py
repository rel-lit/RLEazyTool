"""层内 / 全局 cross 排序单元测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.layout_geometry import CROSS_STEP  # noqa: E402
from core.layout_ordering import (  # noqa: E402
    _sibling_offsets,
    assign_merged_layer_ordering,
)


class LayoutOrderingTest(unittest.TestCase):
    def test_sibling_offsets(self) -> None:
        self.assertEqual(_sibling_offsets(2), [0.0, 0.5])
        self.assertAlmostEqual(_sibling_offsets(3)[1], 1.0 / 3.0)
        self.assertAlmostEqual(_sibling_offsets(3)[2], 2.0 / 3.0)

    def test_layer_by_layer_integer_rank(self) -> None:
        layers = {
            "supply:a": 0,
            "prod:l": 1,
            "prod:r": 1,
            "prod:m": 2,
            "sink:t": 3,
        }
        edges = [
            ("supply:a", "prod:l"),
            ("supply:a", "prod:r"),
            ("prod:l", "prod:m"),
            ("prod:r", "prod:m"),
            ("prod:m", "sink:t"),
        ]
        result = assign_merged_layer_ordering(layers, edges, ["sink:t"])
        self.assertEqual(result.intra_layer_rank["sink:t"], 1)
        self.assertLess(result.intra_layer_rank["prod:l"], result.intra_layer_rank["prod:r"])
        self.assertIn("prod:l", result.intra_layer_frac)

    def test_same_layer_min_spacing(self) -> None:
        layers = {"supply:a": 0, "supply:b": 0, "supply:c": 0}
        result = assign_merged_layer_ordering(layers, [], [])
        vals = sorted(result.cross.values())
        for i in range(1, len(vals)):
            self.assertGreaterEqual(vals[i] - vals[i - 1], CROSS_STEP - 1e-6)


if __name__ == "__main__":
    unittest.main()
