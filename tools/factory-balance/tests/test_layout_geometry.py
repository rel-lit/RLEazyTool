"""布局几何单元测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.layout_geometry import (  # noqa: E402
    assign_rows_within_layers,
    flow_ports,
    node_position,
)
from models.schemas import PrimaryDirection  # noqa: E402


class LayoutGeometryTest(unittest.TestCase):
    def test_lr_places_layer_on_x(self) -> None:
        pos = node_position(0, 2, PrimaryDirection.LEFT_TO_RIGHT)
        self.assertGreater(pos.x, 0)
        self.assertEqual(pos.y, 200)

    def test_tb_places_layer_on_y(self) -> None:
        pos = node_position(1, 3, PrimaryDirection.TOP_TO_BOTTOM)
        self.assertEqual(pos.x, 660)
        self.assertEqual(pos.y, 440)

    def test_rows_are_per_layer(self) -> None:
        layers = {"supply:a": 0, "supply:b": 0, "prod:c": 1, "prod:d": 1}
        rows = assign_rows_within_layers(layers)
        self.assertEqual(rows["supply:a"], 0)
        self.assertEqual(rows["supply:b"], 1)
        self.assertEqual(rows["prod:c"], 0)
        self.assertEqual(rows["prod:d"], 1)

    def test_flow_ports_lr(self) -> None:
        self.assertEqual(flow_ports(PrimaryDirection.LEFT_TO_RIGHT), ("right", "left"))


if __name__ == "__main__":
    unittest.main()
