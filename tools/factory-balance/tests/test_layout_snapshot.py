"""Layer P 布局快照 upsert 测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.layout_engine import compute_layout  # noqa: E402
from db.connection import init_db  # noqa: E402
from db.layout_snapshot_store import (  # noqa: E402
    build_layout_key,
    clear_layout_snapshots,
    get_layout_snapshot,
    upsert_layout_snapshot,
)
from models.schemas import (  # noqa: E402
    LayoutComputeRequest,
    LayoutComputeResponse,
    LayoutOptions,
    LayoutSnapshotUpsert,
    LayoutTarget,
    Position,
    SupplyMode,
    UserNodePosition,
)


class LayoutSnapshotStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        init_db()
        clear_layout_snapshots()
        self.req = LayoutComputeRequest(
            targets=[LayoutTarget(item="electronic-circuit")],
            supply_mode=SupplyMode.RAW,
            layout_options=LayoutOptions(),
        )
        self.result = compute_layout(self.req)

    def test_build_layout_key_stable(self) -> None:
        k1 = build_layout_key(self.req, save_key="save-a")
        k2 = build_layout_key(self.req, save_key="save-a")
        k3 = build_layout_key(self.req, save_key="save-b")
        self.assertEqual(k1, k2)
        self.assertNotEqual(k1, k3)

    def test_upsert_overwrites_same_key(self) -> None:
        snap = LayoutSnapshotUpsert(
            request=self.req,
            response=self.result,
            user_positions={"copper-cable": UserNodePosition(x=10, y=20)},
        )
        first = upsert_layout_snapshot(snap, save_key="sk1", item_labels={})
        snap.user_positions = {"copper-cable": UserNodePosition(x=99, y=88)}
        second = upsert_layout_snapshot(snap, save_key="sk1", item_labels={})
        self.assertEqual(first["layout_key"], second["layout_key"])
        row = get_layout_snapshot(first["id"])
        assert row is not None
        self.assertEqual(row["user_positions"]["copper-cable"]["x"], 99)

    def test_impossible_response_still_storable_if_caller_sends(self) -> None:
        empty = LayoutComputeResponse(
            nodes=[],
            edges=[],
            tap_orders=[],
            warnings=[],
            analysis={"impossible": True},
        )
        snap = LayoutSnapshotUpsert(request=self.req, response=empty)
        row = upsert_layout_snapshot(snap, item_labels={})
        self.assertIn("id", row)


if __name__ == "__main__":
    unittest.main()
