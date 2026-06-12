"""版本解析测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from db.version_resolver import normalize_factorio_version, resolve_factorio_version  # noqa: E402


class VersionResolverTest(unittest.TestCase):
    def test_normalize_save_header_version(self) -> None:
        self.assertEqual(normalize_factorio_version("2.0.76.0"), "2.0.76")
        self.assertEqual(normalize_factorio_version("2.0.76"), "2.0.76")
        self.assertIsNone(normalize_factorio_version("unknown"))

    def test_resolve_prefers_log_when_save_invalid(self) -> None:
        fake_save = Path(__file__).parent / "nonexistent.zip"
        ver = resolve_factorio_version(fake_save)
        self.assertTrue(ver == "unknown" or ver.count(".") >= 2)


if __name__ == "__main__":
    unittest.main()
