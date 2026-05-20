"""纯解析：输入字符串 -> (Action, payload)。无副作用。"""

from __future__ import annotations

from typing import Any

from actions import Action


def _is_exc_command(user_input: str) -> bool:
    s = user_input.strip().lower()
    return s == "exc" or s.startswith("exc ")


def _is_this_command(user_input: str) -> bool:
    s = user_input.strip().lower()
    return s == "this" or s.startswith("this ")


def _parse_this_command(user_input: str) -> tuple[Action, Any]:
    parts = user_input.strip().split()
    low = [p.lower() for p in parts]
    if len(parts) == 1:
        return Action.THIS, ("toggle", None)
    if len(parts) == 2:
        if low[1] == "0":
            return Action.THIS, ("set_depth", 0)
        if low[1] == "max":
            return Action.THIS, ("set_depth", None)
        try:
            n = int(parts[1])
            if n < 0:
                return Action.THIS_INVALID, None
            return Action.THIS, ("set_depth", n)
        except ValueError:
            pass
    if low[1] == "ll":
        if len(parts) == 2:
            return Action.THIS, ("list", 0)
        if len(parts) == 3 and low[2] == "all":
            return Action.THIS, ("list_all", None)
        if len(parts) == 3:
            try:
                return Action.THIS, ("list", int(parts[2]))
            except ValueError:
                return Action.THIS_INVALID, None
        return Action.THIS_INVALID, None
    if low[1] == "a" and len(parts) >= 2:
        return Action.THIS, ("include", parts[2:])
    if low[1] == "s":
        if len(parts) == 2:
            return Action.THIS, ("exclude_usage", None)
        if len(parts) >= 3:
            return Action.THIS, ("exclude", parts[2:])
        return Action.THIS_INVALID, None
    return Action.THIS_INVALID, None


def _is_c_command(user_input: str) -> bool:
    s = user_input.strip().lower()
    return s == "c" or s.startswith("c ")


def _parse_c_command(user_input: str) -> tuple[Action, Any]:
    parts = user_input.strip().split()
    low = [p.lower() for p in parts]
    if len(parts) == 1:
        return Action.CHOOSE, ("toggle", None)
    if len(parts) == 2 and low[1] == "ll":
        return Action.CHOOSE, ("list", None)
    if low[1] == "limit":
        if len(parts) == 2:
            return Action.CHOOSE, ("limit_show", None)
        if len(parts) == 3:
            return Action.CHOOSE, ("limit_set", parts[2])
        return Action.CHOOSE_INVALID, None
    if len(parts) == 2 and low[1] == "all":
        return Action.CHOOSE, ("select_all", None)
    if low[1] == "s":
        if len(parts) == 2:
            return Action.CHOOSE, ("deselect_usage", None)
        if len(parts) == 3 and low[2] == "all":
            return Action.CHOOSE, ("deselect_all", None)
        if len(parts) >= 3:
            return Action.CHOOSE, ("deselect", parts[2:])
        return Action.CHOOSE_INVALID, None
    return Action.CHOOSE, ("select", parts[1:])


def parse_input(user_input: str, history_length: int) -> tuple[Action, Any]:
    user_input = user_input.strip()
    if user_input.lower().startswith("mod "):
        return Action.MOD, user_input.split()
    if _is_c_command(user_input):
        action, payload = _parse_c_command(user_input)
        if action == Action.CHOOSE_INVALID:
            return action, None
        return action, payload
    if _is_this_command(user_input):
        action, payload = _parse_this_command(user_input)
        if action == Action.THIS_INVALID:
            return action, None
        return action, payload
    if user_input.lower() == "q":
        return Action.QUIT, None
    if user_input.lower() == "help":
        return Action.HELP, None
    if user_input.lower() == "m":
        return Action.HISTORY, None
    if user_input.lower() == "ll":
        return Action.LIST_DIRS, None
    if user_input.lower() == "r":
        return Action.CONTINUOUS_MODE, None
    if (
        user_input.isdigit()
        and 1 <= int(user_input) <= history_length
    ):
        return Action.SWITCH_HISTORY, int(user_input) - 1
    if user_input == "":
        return Action.MERGE, None
    if user_input.startswith('"') and user_input.endswith('"'):
        user_input = user_input[1:-1]
    if ":" in user_input:
        return Action.SWITCH_ABS, user_input
    if user_input.startswith("\\") or user_input.startswith("/"):
        return Action.SWITCH_REL, user_input
    if _is_exc_command(user_input):
        parts = user_input.strip().split()
        if len(parts) == 1:
            return Action.EXC_LAST, None
        if len(parts) >= 3 and parts[1] == "a":
            return Action.EXC_ADD, (parts[2], parts[3:])
        if len(parts) == 3 and parts[1] == "d":
            return Action.EXC_DEL, parts[2]
        if len(parts) == 3 and parts[1] == "u":
            return Action.EXC_USE, parts[2]
        if len(parts) == 2 and parts[1] == "q":
            return Action.EXC_DISABLE, None
        if len(parts) == 2 and parts[1] == "ll":
            return Action.EXC_LIST, None
        if len(parts) == 4 and parts[1] == "case":
            return Action.EXC_CASE, (parts[2], parts[3])
        return Action.EXC_INVALID, None
    return Action.INVALID, user_input
