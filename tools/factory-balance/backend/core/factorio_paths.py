"""Factorio 用户目录、可执行文件与存档路径。"""

from __future__ import annotations

import json
import os
import re
import winreg
from dataclasses import dataclass
from pathlib import Path

TOOL_CONFIG = Path(__file__).resolve().parent.parent.parent / "factorio.local.json"
USER_CONFIG = Path.home() / ".rleazytool" / "factory-balance" / "config.json"


@dataclass
class FactorioPaths:
    user_data: Path
    saves_dir: Path
    mods_dir: Path
    script_output_dir: Path
    player_data_file: Path
    executable: Path | None
    config_file: Path | None
    executable_source: str | None = None

    @property
    def progress_export_file(self) -> Path:
        return self.script_output_dir / "factory-balance-progress.json"


def default_user_data_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Factorio"
    return Path.home() / "AppData" / "Roaming" / "Factorio"


def _read_config_paths(config_ini: Path) -> tuple[Path | None, Path | None]:
    if not config_ini.is_file():
        return None, None
    read_data: Path | None = None
    write_data: Path | None = None
    for line in config_ini.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("read-data="):
            val = line.split("=", 1)[1].strip()
            if val and not val.startswith("__PATH__"):
                read_data = Path(val)
        elif line.startswith("write-data="):
            val = line.split("=", 1)[1].strip()
            if val and not val.startswith("__PATH__"):
                write_data = Path(val)
    return read_data, write_data


def _load_saved_executable() -> Path | None:
    for cfg in (TOOL_CONFIG, USER_CONFIG):
        if not cfg.is_file():
            continue
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        exe = data.get("factorio_exe") or data.get("FACTORIO_EXE")
        if exe and Path(exe).is_file():
            return Path(exe)
    return None


def save_executable_path(exe: Path) -> None:
    """记住已检测到的 Factorio 路径（供下次启动）。"""
    payload = {"factorio_exe": str(exe.resolve())}
    TOOL_CONFIG.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _find_executable_from_install_dir(install_dir: Path) -> Path | None:
    candidates = [
        install_dir / "bin" / "x64" / "Factorio.exe",
        install_dir / "bin" / "x64" / "factorio.exe",
        install_dir / "factorio.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _steam_library_roots() -> list[Path]:
    roots: list[Path] = [
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
        Path(r"D:\Steam"),
        Path(r"D:\SteamLibrary"),
        Path(r"E:\SteamLibrary"),
    ]
    vdf_paths: list[Path] = []
    for steam in roots:
        vdf = steam / "steamapps" / "libraryfolders.vdf"
        if vdf.is_file():
            vdf_paths.append(vdf)

    libraries: list[Path] = []
    for vdf in vdf_paths:
        try:
            text = vdf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in re.finditer(r'"path"\s+"([^"]+)"', text):
            lib = Path(match.group(1).replace("\\\\", "\\"))
            libraries.append(lib / "steamapps" / "common" / "Factorio")

    # 常见非标准 Steam 库目录名（如 D:\game store\steamapps\...）
    for drive in ("C", "D", "E", "F"):
        for name in ("game store", "Games", "SteamLibrary", "Steam"):
            candidate = Path(f"{drive}:/{name}/steamapps/common/Factorio")
            libraries.append(candidate)

    return libraries


def _find_executable_from_log(user_data: Path) -> Path | None:
    for log_name in ("factorio-current.log", "factorio-previous.log"):
        log_path = user_data / log_name
        if not log_path.is_file():
            continue
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        m = re.search(r'Program arguments:\s+"([^"]+\.exe)"', text, re.IGNORECASE)
        if m:
            exe = Path(m.group(1))
            if exe.is_file():
                return exe

        m = re.search(r"Binaries path:\s+(.+)", text)
        if m:
            bin_dir = Path(m.group(1).strip())
            for name in ("Factorio.exe", "factorio.exe"):
                exe = bin_dir / "x64" / name
                if exe.is_file():
                    return exe
    return None


def _find_executable(user_data: Path | None = None) -> tuple[Path | None, str | None]:
    env = os.environ.get("FACTORIO_EXE")
    if env and Path(env).is_file():
        return Path(env), "env"

    saved = _load_saved_executable()
    if saved:
        return saved, "config"

    user = user_data or default_user_data_dir()
    from_log = _find_executable_from_log(user)
    if from_log:
        return from_log, "log"

    for root in _steam_library_roots():
        exe = _find_executable_from_install_dir(root)
        if exe:
            return exe, "steam"

    try:
        for hive in (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 427520",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 427520",
        ):
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, hive) as key:
                install, _ = winreg.QueryValueEx(key, "InstallLocation")
                if install:
                    exe = _find_executable_from_install_dir(Path(install))
                    if exe:
                        return exe, "registry"
    except OSError:
        pass

    return None, None


def load_paths(user_data: Path | None = None, executable: Path | None = None) -> FactorioPaths:
    user = user_data or default_user_data_dir()
    config_file = user / "config" / "config.ini"
    _, write_data = _read_config_paths(config_file)
    if write_data:
        user = write_data

    saves = user / "saves"
    mods = user / "mods"
    script_output = user / "script-output"
    script_output.mkdir(parents=True, exist_ok=True)

    source: str | None = None
    if executable is not None:
        exe = executable
        source = "manual"
    else:
        exe, source = _find_executable(user)

    if exe and source in {"log", "steam", "registry"}:
        try:
            save_executable_path(exe)
        except OSError:
            pass

    return FactorioPaths(
        user_data=user,
        saves_dir=saves,
        mods_dir=mods,
        script_output_dir=script_output,
        player_data_file=user / "player-data.json",
        executable=exe,
        config_file=config_file if config_file.is_file() else None,
        executable_source=source,
    )


def read_last_played_save_name(user_data: Path | None = None) -> str | None:
    paths = load_paths(user_data)
    if not paths.player_data_file.is_file():
        return None
    try:
        data = json.loads(paths.player_data_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    last = data.get("last-played") or {}
    name = last.get("save-name")
    return str(name) if name else None
