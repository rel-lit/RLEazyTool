"""layout analysis 元数据单元测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.layout_analysis import build_layout_analysis_meta  # noqa: E402


class LayoutAnalysisMetaTest(unittest.TestCase):
    def test_demoted_outputs_derived_from_declared_minus_effective(self) -> None:
        meta = build_layout_analysis_meta(
            declared_outputs=["advanced-circuit", "electronic-circuit"],
            terminals=["advanced-circuit"],
            analysis_items={"advanced-circuit", "electronic-circuit", "copper-cable"},
            recipe_assignments={},
            pseudo_external=set(),
            impossible=False,
        )
        self.assertEqual(meta["effective_terminals"], ["advanced-circuit"])
        self.assertEqual(meta["terminals"], ["advanced-circuit"])
        self.assertEqual(meta["demoted_outputs"], ["electronic-circuit"])
        self.assertEqual(meta["pseudo_pure_sources"], [])
        self.assertEqual(meta["pseudo_external"], [])


if __name__ == "__main__":
    unittest.main()
