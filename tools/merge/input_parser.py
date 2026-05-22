"""纯解析：输入字符串 -> (Action, payload)。无副作用。"""

from __future__ import annotations

from typing import Any

from actions import Action
from repl_command_parser import parse_with_combinators


def parse_input(user_input: str, history_length: int) -> tuple[Action, Any]:
    return parse_with_combinators(user_input, history_length)
