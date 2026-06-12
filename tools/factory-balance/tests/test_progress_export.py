"""progress_export 命令构建测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.progress_export import _build_export_command, read_current_map_tick  # noqa: E402


class ExportCommandTest(unittest.TestCase):
    def test_uses_load_game_with_target_tick(self) -> None:
        cmd = _build_export_command(
            Path("D:/game store/Factorio/bin/x64/Factorio.exe"),
            Path("C:/saves/test.zip"),
            12169022,
        )
        self.assertIn("--load-game", cmd)
        self.assertIn("--until-tick", cmd)
        idx = cmd.index("--until-tick")
        self.assertEqual(cmd[idx + 1], "12169022")
        self.assertNotIn("--benchmark", cmd)


if __name__ == "__main__":
    unittest.main()
