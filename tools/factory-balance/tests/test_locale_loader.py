"""locale 加载测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from core.locale_loader import parse_factorio_cfg, resolve_game_data_dir  # noqa: E402
from core.factorio_paths import load_paths  # noqa: E402
from core.locale_loader import load_locale_from_install, locale_has_names  # noqa: E402


class LocaleLoaderTest(unittest.TestCase):
    def test_parse_cfg_item_name(self) -> None:
        sample = Path(__file__).parent / "fixtures" / "sample-locale.cfg"
        tables = parse_factorio_cfg(sample)
        self.assertEqual(tables["item"]["copper-plate"], "铜板")
        self.assertEqual(tables["recipe"]["electronic-circuit"], "绿板")

    def test_load_from_install_if_factorio_present(self) -> None:
        paths = load_paths()
        if paths.executable is None:
            self.skipTest("未配置 Factorio 可执行文件")
        locale = load_locale_from_install(paths)
        self.assertTrue(locale_has_names(locale))
        copper = locale["item"]["copper-plate"]["localised_name"][0]
        self.assertEqual(copper, "铜板")

    def test_resolve_data_dir(self) -> None:
        paths = load_paths()
        if paths.executable is None:
            self.skipTest("未配置 Factorio 可执行文件")
        data_dir = resolve_game_data_dir(paths.executable)
        self.assertTrue((data_dir / "base" / "locale" / "zh-CN" / "base.cfg").is_file())


if __name__ == "__main__":
    unittest.main()
