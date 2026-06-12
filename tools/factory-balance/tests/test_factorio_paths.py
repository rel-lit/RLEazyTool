"""factorio_paths 检测测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.factorio_paths import _find_executable_from_log, default_user_data_dir, load_paths  # noqa: E402


class FactorioPathsTest(unittest.TestCase):
    def test_find_exe_from_current_log(self) -> None:
        user = default_user_data_dir()
        exe = _find_executable_from_log(user)
        if (user / "factorio-current.log").is_file():
            self.assertIsNotNone(exe, "应从 factorio-current.log 解析到 Factorio.exe")
            self.assertTrue(exe.is_file())

    def test_load_paths_finds_executable(self) -> None:
        paths = load_paths()
        if (default_user_data_dir() / "factorio-current.log").is_file():
            self.assertIsNotNone(paths.executable)
            self.assertIn(paths.executable_source, {"log", "config", "env", "steam", "registry"})


if __name__ == "__main__":
    unittest.main()
