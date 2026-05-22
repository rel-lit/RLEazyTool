"""解析器产出的指令类型（与具体处理逻辑解耦）。"""

from enum import StrEnum


class Action(StrEnum):
    MOD = "mod"
    QUIT = "quit"
    HELP = "help"
    HISTORY = "history"
    LIST_DIRS = "list_dirs"
    THIS = "this"
    THIS_INVALID = "this_invalid"
    CONTINUOUS_MODE = "continuous_mode"
    SWITCH_HISTORY = "switch_history"
    MERGE = "merge"
    SWITCH_ABS = "switch_abs"
    SWITCH_REL = "switch_rel"
    EXC = "exc"
    EXC_INVALID = "exc_invalid"
    CHOOSE = "choose"
    CHOOSE_INVALID = "choose_invalid"
    ANA = "ana"
    INVALID = "invalid"
