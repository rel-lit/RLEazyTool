"""REPL 指令：parsy 组合子解析 → (Action, payload)。"""

from __future__ import annotations

import re
import shlex
from typing import Any, Callable

import parsy

from actions import Action
from exclude_rules import FILE_RULE_KINDS

ws = parsy.regex(r"\s+")
opt_ws = parsy.regex(r"\s*")
eof = parsy.eof
# 保留左侧解析结果，仅消费尾随空白与 EOF
_end = opt_ws << eof


def _ci_lit(text: str) -> parsy.Parser:
    """大小写不敏感关键字（不吞尾随空白，由 ws / opt_ws 显式处理）。"""
    return parsy.regex(r"(?i)" + re.escape(text))


def _token_word() -> parsy.Parser:
    return parsy.regex(r"\S+")


def _int_positive() -> parsy.Parser:
    return parsy.regex(r"\d+").map(int).bind(
        lambda n: parsy.success(n) if n >= 0 else parsy.fail("负数")
    )


def _rest_tokens() -> parsy.Parser:
    return (
        opt_ws
        >> parsy.regex(r".+")
        .map(lambda s: s.split())
        .optional([])
    )


# --- ana ---
_ana_show = (_ci_lit("ana") >> ws >> _ci_lit("show") >> opt_ws >> eof).map(
    lambda _: (Action.ANA, ("show", None))
)
_ana_toggle = (_ci_lit("ana") >> opt_ws >> eof).map(
    lambda _: (Action.ANA, ("toggle", None))
)

# --- 基础 ---
_basic = parsy.alt(
    (_ci_lit("q") >> opt_ws >> eof).map(lambda _: (Action.QUIT, None)),
    (_ci_lit("help") >> opt_ws >> eof).map(lambda _: (Action.HELP, None)),
    (_ci_lit("m") >> opt_ws >> eof).map(lambda _: (Action.HISTORY, None)),
    (_ci_lit("ll") >> opt_ws >> eof).map(lambda _: (Action.LIST_DIRS, None)),
    (_ci_lit("r") >> opt_ws >> eof).map(lambda _: (Action.CONTINUOUS_MODE, None)),
)

# --- this ---
_this_toggle = (_ci_lit("this") >> opt_ws >> eof).map(
    lambda _: (Action.THIS, ("toggle", None))
)
_this_depth = (
    _ci_lit("this")
    >> ws
    >> parsy.alt(
        _ci_lit("max").map(lambda _: None),
        _ci_lit("0").map(lambda _: 0),
        _int_positive(),
    )
    << _end
).map(lambda d: (Action.THIS, ("set_depth", d)))

_this_ll_all = (
    _ci_lit("this") >> ws >> _ci_lit("ll") >> ws >> _ci_lit("all") >> opt_ws >> eof
).map(lambda _: (Action.THIS, ("list_all", None)))

_this_ll_n = (
    _ci_lit("this")
    >> ws
    >> _ci_lit("ll")
    >> ws
    >> _int_positive()
    << _end
).map(lambda n: (Action.THIS, ("list", n)))

_this_ll = (_ci_lit("this") >> ws >> _ci_lit("ll") >> opt_ws >> eof).map(
    lambda _: (Action.THIS, ("list", 0))
)

_this_include = (
    _ci_lit("this") >> ws >> _ci_lit("a") >> ws >> _rest_tokens() << _end
).map(lambda paths: (Action.THIS, ("include", paths)))

_this_exclude_usage = (
    _ci_lit("this") >> ws >> _ci_lit("s") >> opt_ws >> eof
).map(lambda _: (Action.THIS, ("exclude_usage", None)))

_this_exclude = (
    _ci_lit("this") >> ws >> _ci_lit("s") >> ws >> _rest_tokens() << _end
).map(lambda paths: (Action.THIS, ("exclude", paths)))

_this = parsy.alt(
    _this_depth,
    _this_ll_all,
    _this_ll_n,
    _this_ll,
    _this_include,
    _this_exclude_usage,
    _this_exclude,
    _this_toggle,
)

# --- c ---
_c_toggle = (_ci_lit("c") >> opt_ws >> eof).map(
    lambda _: (Action.CHOOSE, ("toggle", None))
)
_c_ll = (_ci_lit("c") >> ws >> _ci_lit("ll") >> opt_ws >> eof).map(
    lambda _: (Action.CHOOSE, ("list", None))
)
_c_limit_show = (_ci_lit("c") >> ws >> _ci_lit("limit") >> opt_ws >> eof).map(
    lambda _: (Action.CHOOSE, ("limit_show", None))
)
_c_limit_set = (
    _ci_lit("c") >> ws >> _ci_lit("limit") >> ws >> _token_word() << _end
).map(lambda n: (Action.CHOOSE, ("limit_set", n)))
_c_all = (_ci_lit("c") >> ws >> _ci_lit("all") >> opt_ws >> eof).map(
    lambda _: (Action.CHOOSE, ("select_all", None))
)
_c_s_usage = (_ci_lit("c") >> ws >> _ci_lit("s") >> opt_ws >> eof).map(
    lambda _: (Action.CHOOSE, ("deselect_usage", None))
)
_c_s_all = (
    _ci_lit("c") >> ws >> _ci_lit("s") >> ws >> _ci_lit("all") >> opt_ws >> eof
).map(lambda _: (Action.CHOOSE, ("deselect_all", None)))
_c_s = (
    _ci_lit("c") >> ws >> _ci_lit("s") >> ws >> _rest_tokens() << _end
).map(lambda ids: (Action.CHOOSE, ("deselect", ids)))
_c_select = (_ci_lit("c") >> ws >> _rest_tokens() << _end).map(
    lambda ids: (Action.CHOOSE, ("select", ids))
)

_choose = parsy.alt(
    _c_limit_set,
    _c_limit_show,
    _c_ll,
    _c_all,
    _c_s_all,
    _c_s_usage,
    _c_s,
    _c_select,
    _c_toggle,
)


def _parse_exc_shlex(line: str) -> tuple[Action, Any]:
    """exc 含引号路径，保留 shlex。"""
    try:
        parts = shlex.split(line.strip(), posix=False)
    except ValueError:
        return Action.EXC_INVALID, None
    if not parts or parts[0].lower() != "exc":
        return Action.EXC_INVALID, None
    low = [p.lower() for p in parts]
    if len(parts) == 1:
        return Action.EXC, ("toggle", None)
    if len(parts) == 3 and low[1] == "u":
        return Action.EXC, ("use", parts[2])
    if len(parts) == 3 and low[1] == "a":
        return Action.EXC, ("group_add", parts[2])
    if len(parts) == 3 and low[1] == "d":
        return Action.EXC, ("group_del", parts[2])
    if low[1] == "gitignore":
        if len(parts) == 2:
            return Action.EXC, ("gitignore_show", None)
        if len(parts) == 3 and low[2] == "on":
            return Action.EXC, ("gitignore_on", None)
        if len(parts) == 3 and low[2] == "off":
            return Action.EXC, ("gitignore_off", None)
    if low[1] == "ll":
        if len(parts) == 2:
            return Action.EXC, ("list", None)
        if len(parts) == 3 and low[2] == "now":
            return Action.EXC, ("list_now", None)
    if low[1] == "dir" and len(parts) >= 4:
        group = parts[3]
        if low[2] == "a":
            return Action.EXC, ("dir_add", (group, parts[4:]))
        if low[2] == "d":
            return Action.EXC, ("dir_del", (group, parts[4:]))
        if low[2] == "clr" and len(parts) == 4:
            return Action.EXC, ("dir_clr", group)
        if low[2] == "ll" and len(parts) == 4:
            return Action.EXC, ("dir_ll", group)
    if low[1] == "f" and len(parts) >= 4:
        group = parts[3]
        if low[2] == "a" and len(parts) >= 6:
            kind = parts[4].lower()
            if kind not in FILE_RULE_KINDS:
                return Action.EXC_INVALID, None
            return Action.EXC, ("f_add", (group, kind, parts[5]))
        if low[2] == "clr" and len(parts) == 4:
            return Action.EXC, ("f_clr", group)
        if low[2] == "ll" and len(parts) == 4:
            return Action.EXC, ("f_ll", group)
        if low[2] == "d" and len(parts) >= 5:
            if parts[4].isdigit():
                indices = [int(x) for x in parts[4:] if x.isdigit()]
                if indices:
                    return Action.EXC, ("f_del_index", (group, indices))
            if len(parts) >= 6 and parts[4].lower() in FILE_RULE_KINDS:
                return Action.EXC, (
                    "f_del_rule",
                    (group, parts[4].lower(), parts[5]),
                )
    return Action.EXC_INVALID, None


def _parse_mod(line: str) -> tuple[Action, Any]:
    return Action.MOD, line.split()


def _parse_history(line: str, history_length: int) -> tuple[Action, Any] | None:
    if line.isdigit() and 1 <= int(line) <= history_length:
        return Action.SWITCH_HISTORY, int(line) - 1
    return None


def _parse_path(line: str) -> tuple[Action, Any] | None:
    if line.startswith('"') and line.endswith('"'):
        return Action.SWITCH_ABS, line[1:-1]
    if ":" in line:
        return Action.SWITCH_ABS, line
    if line.startswith("\\") or line.startswith("/"):
        return Action.SWITCH_REL, line
    return None


def _wrap_this(result: tuple[Action, Any]) -> tuple[Action, Any]:
    action, payload = result
    if action != Action.THIS:
        return action, payload
    cmd, data = payload
    if cmd == "set_depth" and data is not None and data < 0:
        return Action.THIS_INVALID, None
    return action, payload


def _wrap_choose(result: tuple[Action, Any]) -> tuple[Action, Any]:
    action, payload = result
    if action == Action.CHOOSE_INVALID:
        return action, None
    return action, payload


_COMBINED = parsy.alt(
    _ana_show,
    _ana_toggle,
    _choose.map(_wrap_choose),
    _this.map(_wrap_this),
    _basic,
)


def parse_with_combinators(
    user_input: str, history_length: int
) -> tuple[Action, Any]:
    line = user_input.strip()
    if not line:
        return Action.MERGE, None
    low = line.lower()
    if low.startswith("mod "):
        return _parse_mod(line)
    if low.startswith("exc") or low == "exc":
        return _parse_exc_shlex(line)
    hist = _parse_history(line, history_length)
    if hist:
        return hist
    path = _parse_path(line)
    if path:
        return path
    try:
        return _COMBINED.parse(line)
    except parsy.ParseError:
        return Action.INVALID, line
