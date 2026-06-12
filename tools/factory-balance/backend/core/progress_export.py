"""安装 companion 模组并通过 Factorio 导出存档进度 → SQLite。"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .factorio_paths import FactorioPaths, load_paths
from .save_index import resolve_save_path, _save_display_name
from db.ingest import ensure_environment, get_snapshot_id_for_env
from db.save_store import upsert_save_progress, is_save_progress_stale, has_save_progress

COMPANION_SRC = Path(__file__).resolve().parent.parent.parent / "companion-mod" / "factory-balance-sync"
COMPANION_DIR_NAME = "factory-balance-sync_0.1.1"
COMPANION_MOD_NAME = "factory-balance-sync"
EXPORT_FILENAME = "factory-balance-progress.json"
ERROR_FILENAME = "factory-balance-error.txt"
EXPORT_TIMEOUT_SEC = 180
TICK_ADVANCE = 60


def _enable_mod_in_list(paths: FactorioPaths) -> None:
    mod_list_path = paths.mods_dir / "mod-list.json"
    data: dict = {"mods": []}
    if mod_list_path.is_file():
        try:
            data = json.loads(mod_list_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {"mods": []}
    mods: list[dict] = list(data.get("mods") or [])
    found = False
    for entry in mods:
        if entry.get("name") == COMPANION_MOD_NAME:
            entry["enabled"] = True
            found = True
            break
    if not found:
        mods.append({"name": COMPANION_MOD_NAME, "enabled": True})
    data["mods"] = mods
    mod_list_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def install_companion_mod(paths: FactorioPaths | None = None) -> Path:
    paths = paths or load_paths()
    paths.mods_dir.mkdir(parents=True, exist_ok=True)
    dest = paths.mods_dir / COMPANION_DIR_NAME
    if dest.is_dir():
        shutil.rmtree(dest)
    shutil.copytree(COMPANION_SRC, dest)
    _enable_mod_in_list(paths)
    return dest


def _run_factorio(args: list[str], timeout: int = EXPORT_TIMEOUT_SEC) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def _combined_output(proc: subprocess.CompletedProcess[str]) -> str:
    return f"{proc.stdout or ''}\n{proc.stderr or ''}"


def _build_export_command(exe: Path, save_path: Path, target_tick: int) -> list[str]:
    return [
        str(exe),
        "--load-game",
        str(save_path),
        "--until-tick",
        str(target_tick),
        "--disable-audio",
    ]


def read_current_map_tick(exe: Path, save_path: Path) -> int:
    proc = _run_factorio(
        [str(exe), "--load-game", str(save_path), "--until-tick", "1", "--disable-audio"],
        timeout=120,
    )
    text = _combined_output(proc)
    match = re.search(r"current map tick is (\d+)", text)
    if match:
        return int(match.group(1))
    raise RuntimeError(f"无法解析存档当前 tick。Factorio 输出末尾:\n{text.strip()[-800:]}")


def _parse_failure_hints(proc: subprocess.CompletedProcess[str]) -> list[str]:
    combined = _combined_output(proc)
    hints: list[str] = []
    error_path = load_paths().script_output_dir / ERROR_FILENAME
    if error_path.is_file():
        try:
            hints.append(f"模组错误: {error_path.read_text(encoding='utf-8').strip()}")
        except OSError:
            pass
    if proc.returncode != 0:
        hints.append(f"Factorio 退出码: {proc.returncode}")
    tail = combined.strip()[-600:]
    if tail:
        hints.append(f"日志片段: {tail}")
    return hints or ["未能生成 factory-balance-progress.json。"]


def _read_export_payload(paths: FactorioPaths) -> dict | None:
    export_file = paths.script_output_dir / EXPORT_FILENAME
    if not export_file.is_file():
        return None
    try:
        return json.loads(export_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def export_progress_from_save(
    save_name_or_path: str,
    paths: FactorioPaths | None = None,
    *,
    install_mod: bool = True,
    reexport: bool = False,
) -> tuple[str | None, list[str]]:
    """返回 (save_key, warnings)。"""
    warnings: list[str] = []
    paths = paths or load_paths()
    save_path = resolve_save_path(save_name_or_path, paths)
    if save_path is None:
        return None, [f"找不到存档: {save_name_or_path}"]

    save_key = _save_display_name(save_path)

    if not reexport and has_save_progress(save_key):
        from db.environment_store import touch_environment
        from db.save_store import get_save_binding

        binding = get_save_binding(save_key)
        if binding:
            touch_environment(binding["env_key"])
        stale = is_save_progress_stale(save_key, save_path)
        if stale:
            return save_key, [
                "存档文件已更新，当前仍使用上次导入的进度；请点击「从存档导入」同步最新进度。"
            ]
        return save_key, ["已从数据库加载存档进度（未启动 Factorio）。"]

    if paths.executable is None:
        return None, ["未找到 Factorio 可执行文件。"]

    try:
        env_key, env_warnings = ensure_environment(paths, save_path=save_path)
    except Exception as e:
        return None, [f"导入配方环境失败: {e}"]
    warnings.extend(env_warnings)

    if install_mod:
        install_companion_mod(paths)

    for name in (EXPORT_FILENAME, ERROR_FILENAME):
        p = paths.script_output_dir / name
        if p.is_file():
            p.unlink()

    warnings.append("在临时副本上导出进度，不会修改您的原存档文件。")

    try:
        with tempfile.TemporaryDirectory(prefix="fb-export-") as tmp_dir:
            temp_save = Path(tmp_dir) / save_path.name
            shutil.copy2(save_path, temp_save)
            original_mtime = save_path.stat().st_mtime

            current_tick = read_current_map_tick(paths.executable, temp_save)
            target_tick = current_tick + TICK_ADVANCE
            warnings.append(
                f"存档 tick={current_tick}，在副本上推进至 {target_tick} 触发导出"
            )

            try:
                proc = _run_factorio(
                    _build_export_command(paths.executable, temp_save, target_tick)
                )
            except subprocess.TimeoutExpired:
                return None, [f"导出超时（>{EXPORT_TIMEOUT_SEC}s）"]
            except OSError as e:
                return None, [f"启动 Factorio 失败: {e}"]

            deadline = time.time() + 15
            payload = None
            while time.time() < deadline:
                payload = _read_export_payload(paths)
                if payload:
                    break
                time.sleep(0.2)

            if not payload:
                return None, _parse_failure_hints(proc)

            snapshot_id = get_snapshot_id_for_env(env_key)
            upsert_save_progress(
                save_key=save_key,
                save_path=save_path,
                env_key=env_key,
                enabled_recipe_names=list(payload.get("enabled_recipes") or []),
                researched_tech_names=list(payload.get("researched_technologies") or []),
                exported_tick=int(payload["exported_at_tick"])
                if payload.get("exported_at_tick") is not None
                else None,
                snapshot_id=snapshot_id,
            )
            # 确认原存档 mtime 未被 Factorio 改动
            try:
                if abs(save_path.stat().st_mtime - original_mtime) > 1:
                    warnings.append(
                        "警告：原存档文件的修改时间与导入前不一致，请确认未被其他程序改动。"
                    )
            except OSError:
                pass

            if not payload.get("enabled_recipes"):
                warnings.append("导出成功但未发现已启用配方。")
            return save_key, warnings
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as e:
        return None, [f"读取存档 tick 失败: {e}"]

    return None, ["导出未完成。"]


def derive_craftable_items(enabled_recipes: list[str], recipe_db) -> list[str]:
    items: set[str] = set()
    for rname in enabled_recipes:
        recipe = recipe_db.recipes.get(rname)
        if not recipe:
            continue
        for prod in recipe.products:
            if prod.type == "item":
                items.add(prod.name)
    return sorted(n for n in items if not n.startswith("parameter-"))
