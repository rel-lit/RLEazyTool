"""布局几何单元测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.layout_geometry import (  # noqa: E402
    CROSS_STAGGER,
    CROSS_STEP,
    assign_brick_cross_positions,
    assign_rows_within_layers,
    flow_ports,
    node_position,
    spread_cross_positions,
    staggered_base_cross,
)
from models.schemas import PrimaryDirection  # noqa: E402


class LayoutGeometryTest(unittest.TestCase):
    def test_lr_places_layer_on_x(self) -> None:
        pos = node_position(0, 2, PrimaryDirection.LEFT_TO_RIGHT)
        self.assertGreater(pos.x, 0)
        self.assertEqual(pos.y, 192.0)
        pos_odd = node_position(1, 2, PrimaryDirection.LEFT_TO_RIGHT)
        self.assertEqual(pos_odd.y, 192.0 + CROSS_STAGGER)

    def test_tb_places_layer_on_y(self) -> None:
        pos = node_position(1, 3, PrimaryDirection.TOP_TO_BOTTOM)
        self.assertEqual(pos.x, staggered_base_cross(1, 3))
        self.assertEqual(pos.y, 384.0)

    def test_rows_are_per_layer(self) -> None:
        layers = {"supply:a": 0, "supply:b": 0, "prod:c": 1, "prod:d": 1}
        rows = assign_rows_within_layers(layers)
        self.assertEqual(rows["supply:a"], 0)
        self.assertEqual(rows["supply:b"], 1)
        self.assertEqual(rows["prod:c"], 0)
        self.assertEqual(rows["prod:d"], 1)

    def test_stagger_offsets_adjacent_layers(self) -> None:
        self.assertEqual(staggered_base_cross(0, 0), 0.0)
        self.assertEqual(staggered_base_cross(1, 0), CROSS_STAGGER)
        self.assertEqual(staggered_base_cross(2, 0), 0.0)

    def test_brick_stagger_breaks_layer_alignment(self) -> None:
        layers = {"a": 0, "b": 1}
        cross = assign_brick_cross_positions(layers, {"a": 1, "b": 1}, [])
        self.assertNotAlmostEqual(cross["a"], cross["b"], places=3)
        self.assertAlmostEqual(abs(cross["a"] - cross["b"]), CROSS_STAGGER, places=3)

    def test_spread_adds_gap_on_backtrack(self) -> None:
        layers = {"a": 3, "b": 1, "c": 1}
        base_rows = {"a": 0, "b": 0, "c": 1}
        cross = spread_cross_positions(layers, base_rows, [["a", "b", "c"]])
        self.assertGreater(cross["b"], cross["a"])
        self.assertGreater(cross["c"], cross["b"])

    def test_flow_ports_lr(self) -> None:
        self.assertEqual(flow_ports(PrimaryDirection.LEFT_TO_RIGHT), ("right", "left"))


if __name__ == "__main__":
    unittest.main()
