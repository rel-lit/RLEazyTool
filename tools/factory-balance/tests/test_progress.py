"""存档与进度相关测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.factorio_paths import read_last_played_save_name  # noqa: E402


class LastPlayedTest(unittest.TestCase):
    def test_read_last_played_from_appdata_if_exists(self) -> None:
        name = read_last_played_save_name()
        if name:
            self.assertIsInstance(name, str)


if __name__ == "__main__":
    unittest.main()
