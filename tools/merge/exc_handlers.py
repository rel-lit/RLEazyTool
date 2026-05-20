"""exc 排除模板：组 / dir / f 子命令。"""

from __future__ import annotations

from typing import Any

from exclude_rules import (
    FILE_RULE_KINDS,
    empty_exclude_group,
    file_rules_from_group,
    norm_skip_dir,
    normalize_exclude_group,
    skip_dirs_from_group,
)
from gitignore_support import (
    GitIgnoreMatcher,
    find_git_root,
    pathspec_available,
)
from models import MergeConfig
from storage import save_config

_FILE_KINDS_HELP = "contains | prefix | suffix | glob | regex"


def _get_group(config: MergeConfig, name: str) -> dict[str, Any] | None:
    if name not in config.exclude_groups:
        return None
    g = normalize_exclude_group(config.exclude_groups[name])
    config.exclude_groups[name] = g
    return g


def _save(config: MergeConfig) -> None:
    save_config(config)


def _activate_exclude_group(config: MergeConfig, name: str) -> None:
    config.current_exclude_group = name
    config.last_exclude_group = name


def _resolve_last_exclude_group(config: MergeConfig) -> str | None:
    name = config.last_exclude_group
    if name and name in config.exclude_groups:
        return name
    return None


def _invalidate_choose_if_active(repl) -> None:
    if hasattr(repl, "_invalidate_choose"):
        repl._invalidate_choose("已修改 exc 排除组")


def handle_exc(repl, payload: tuple[str, object]) -> None:
    cmd, data = payload
    config = repl.config

    if cmd == "gitignore_on":
        if not pathspec_available():
            print(
                "❌ 需要 pathspec 库。请执行: pip install -r tools/merge/requirements.txt"
            )
            return
        config.use_gitignore = True
        _save(config)
        _invalidate_choose_if_active(repl)
        root = find_git_root(repl.current_path)
        if root is None:
            print(
                "✅ 已开启 .gitignore 过滤（当前路径不在 Git 仓库内，合并时不生效）。"
            )
        else:
            matcher = GitIgnoreMatcher.load(repl.current_path)
            n = matcher.pattern_count if matcher else 0
            print(
                f"✅ 已开启 .gitignore 过滤（仓库根: {root}，共 {n} 条规则）。"
            )
        return

    if cmd == "gitignore_off":
        if config.use_gitignore:
            config.use_gitignore = False
            _save(config)
            _invalidate_choose_if_active(repl)
            print("✅ 已关闭 .gitignore 过滤。")
        else:
            print("ℹ️ .gitignore 过滤未开启。")
        return

    if cmd == "gitignore_show":
        if not pathspec_available():
            print("ℹ️ pathspec 未安装，无法解析 .gitignore。")
            return
        print(f"  .gitignore 过滤: {'开' if config.use_gitignore else '关'}")
        root = find_git_root(repl.current_path)
        if root is None:
            print("  当前路径不在 Git 仓库内。")
        else:
            matcher = GitIgnoreMatcher.load(repl.current_path)
            n = matcher.pattern_count if matcher else 0
            print(f"  仓库根: {root}")
            print(f"  已加载规则: {n} 条")
        return

    if cmd == "toggle":
        if config.current_exclude_group:
            old = config.current_exclude_group
            config.last_exclude_group = old
            config.current_exclude_group = None
            _save(config)
            _invalidate_choose_if_active(repl)
            print(
                f"✅ 已关闭排除（组「{old}」仍保留，再次输入 exc 可启用）。"
            )
        else:
            name = _resolve_last_exclude_group(config)
            if not name:
                print(
                    "❌ 没有可启用的排除组。请先 exc a <组名> 新建，"
                    "或 exc <组名> 指定组。"
                )
                return
            _activate_exclude_group(config, name)
            _save(config)
            _invalidate_choose_if_active(repl)
            print(f"✅ 已启用排除组: {name}")
        return

    if cmd == "use":
        name = str(data)
        if name not in config.exclude_groups:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        _activate_exclude_group(config, name)
        _save(config)
        _invalidate_choose_if_active(repl)
        print(f"✅ 已启用排除组: {name}")
        return

    if cmd == "group_add":
        name = str(data)
        if name in config.exclude_groups:
            print(f"❌ 排除组 '{name}' 已存在。")
            return
        config.exclude_groups[name] = empty_exclude_group()
        _save(config)
        print(f"✅ 已新建排除组: {name}")
        return

    if cmd == "group_del":
        name = str(data)
        if name not in config.exclude_groups:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        del config.exclude_groups[name]
        if config.current_exclude_group == name:
            config.current_exclude_group = None
        if config.last_exclude_group == name:
            config.last_exclude_group = None
        _save(config)
        _invalidate_choose_if_active(repl)
        print(f"✅ 已删除排除组: {name}")
        return

    if cmd == "list":
        if not config.exclude_groups:
            print("(无排除组)")
            return
        cur = config.current_exclude_group
        print("\n🛑 排除组列表：")
        for name, raw in config.exclude_groups.items():
            g = normalize_exclude_group(raw)
            config.exclude_groups[name] = g
            mark = " ← 当前" if name == cur else ""
            nd = len(g.get("skip_dirs") or [])
            nf = len(g.get("file_rules") or [])
            print(f"  {name}: {nd} 个跳过目录, {nf} 条文件规则{mark}")
        print()
        return

    if cmd == "list_now":
        cur = config.current_exclude_group
        if not cur or cur not in config.exclude_groups:
            print("ℹ️ 当前未启用排除组。请 exc <组名> 或输入 exc 开关。")
            return
        g = _get_group(config, cur)
        assert g is not None
        print(f"\n🛑 当前排除组: {cur}\n")
        print("  [跳过目录名] (任意层级同名文件夹不扫描)")
        dirs = g.get("skip_dirs") or []
        if not dirs:
            print("    (无，仅程序内置 bin/obj/…)")
        for i, d in enumerate(dirs, 1):
            print(f"    {i}. {d}")
        print("\n  [文件名规则]")
        rules = g.get("file_rules") or []
        if not rules:
            print("    (无)")
        for i, r in enumerate(rules, 1):
            print(f"    {i}. [{r['kind']}] {r['pattern']}")
        print()
        return

    if cmd == "dir_add":
        name, dir_names = data  # type: ignore[misc]
        g = _get_group(config, str(name))
        if g is None:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        added = _add_skip_dirs(g, list(dir_names))  # type: ignore[arg-type]
        _save(config)
        _invalidate_choose_if_active(repl)
        if added:
            print(f"✅ 已追加跳过目录: {', '.join(added)}")
        else:
            print("ℹ️ 无新目录名（已存在或为空）。")
        return

    if cmd == "dir_del":
        name, dir_names = data  # type: ignore[misc]
        g = _get_group(config, str(name))
        if g is None:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        removed = _del_skip_dirs(g, list(dir_names))  # type: ignore[arg-type]
        _save(config)
        _invalidate_choose_if_active(repl)
        if removed:
            print(f"✅ 已移除跳过目录: {', '.join(removed)}")
        else:
            print("ℹ️ 未移除任何项。")
        return

    if cmd == "dir_clr":
        name = str(data)
        g = _get_group(config, name)
        if g is None:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        g["skip_dirs"] = []
        _save(config)
        _invalidate_choose_if_active(repl)
        print(f"✅ 已清空组 '{name}' 的跳过目录（程序内置仍生效）。")
        return

    if cmd == "dir_ll":
        name = str(data)
        g = _get_group(config, name)
        if g is None:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        dirs = g.get("skip_dirs") or []
        print(f"\n[exc dir] 组 '{name}' 跳过目录名:\n")
        if not dirs:
            print("  (无)")
        for i, d in enumerate(dirs, 1):
            print(f"  {i}. {d}")
        print()
        return

    if cmd == "f_add":
        name, kind, pattern = data  # type: ignore[misc]
        kind = str(kind).lower()
        if kind not in FILE_RULE_KINDS:
            print(f"❌ 未知规则类型: {kind}。支持: {_FILE_KINDS_HELP}")
            return
        pattern = str(pattern)
        if not pattern:
            print("❌ pattern 不能为空。")
            return
        g = _get_group(config, str(name))
        if g is None:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        rules: list[dict[str, str]] = list(g.get("file_rules") or [])
        entry = {"kind": kind, "pattern": pattern}
        if entry in rules:
            print("ℹ️ 相同规则已存在。")
            return
        rules.append(entry)
        g["file_rules"] = rules
        _save(config)
        _invalidate_choose_if_active(repl)
        print(f"✅ 已添加: [{kind}] {pattern}")
        return

    if cmd == "f_del_index":
        name, indices = data  # type: ignore[misc]
        g = _get_group(config, str(name))
        if g is None:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        rules: list[dict[str, str]] = list(g.get("file_rules") or [])
        if not rules:
            print("❌ 该组没有文件规则。")
            return
        to_remove = sorted(
            {int(i) for i in indices if 1 <= int(i) <= len(rules)},
            reverse=True,
        )
        if not to_remove:
            print("❌ 无效序号。")
            return
        for idx in to_remove:
            del rules[idx - 1]
        g["file_rules"] = rules
        _save(config)
        _invalidate_choose_if_active(repl)
        print(f"✅ 已删除 {len(to_remove)} 条规则。")
        return

    if cmd == "f_del_rule":
        name, kind, pattern = data  # type: ignore[misc]
        kind = str(kind).lower()
        g = _get_group(config, str(name))
        if g is None:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        entry = {"kind": kind, "pattern": str(pattern)}
        rules = [r for r in (g.get("file_rules") or []) if r != entry]
        if len(rules) == len(g.get("file_rules") or []):
            print("❌ 未找到匹配规则。")
            return
        g["file_rules"] = rules
        _save(config)
        _invalidate_choose_if_active(repl)
        print(f"✅ 已删除: [{kind}] {pattern}")
        return

    if cmd == "f_clr":
        name = str(data)
        g = _get_group(config, name)
        if g is None:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        g["file_rules"] = []
        _save(config)
        _invalidate_choose_if_active(repl)
        print(f"✅ 已清空组 '{name}' 的文件规则。")
        return

    if cmd == "f_ll":
        name = str(data)
        g = _get_group(config, name)
        if g is None:
            print(f"❌ 排除组 '{name}' 不存在。")
            return
        rules = g.get("file_rules") or []
        print(f"\n[exc f] 组 '{name}' 文件名规则:\n")
        if not rules:
            print("  (无)")
        for i, r in enumerate(rules, 1):
            print(f"  {i}. [{r['kind']}] {r['pattern']}")
        print()
        return

    print(f"⚠️ 未处理的 exc 子命令: {cmd}")


def _add_skip_dirs(group: dict[str, Any], names: list[str]) -> list[str]:
    current = list(group.get("skip_dirs") or [])
    seen = set(current)
    added: list[str] = []
    for raw in names:
        n = norm_skip_dir(raw)
        if not n or n in seen:
            continue
        seen.add(n)
        current.append(n)
        added.append(n)
    group["skip_dirs"] = current
    return added


def _del_skip_dirs(group: dict[str, Any], names: list[str]) -> list[str]:
    remove = {norm_skip_dir(x) for x in names if norm_skip_dir(x)}
    current = list(group.get("skip_dirs") or [])
    new_list = [d for d in current if d not in remove]
    removed = [d for d in current if d in remove]
    group["skip_dirs"] = new_list
    return removed


def exc_filter_from_config(
    config: MergeConfig,
) -> tuple[tuple[str, ...], tuple]:
    """返回 (exc_skip_dirs, exc_file_rules)。"""
    name = config.current_exclude_group
    if not name or name not in config.exclude_groups:
        return (), ()
    g = normalize_exclude_group(config.exclude_groups[name])
    config.exclude_groups[name] = g
    return skip_dirs_from_group(g), file_rules_from_group(g)
