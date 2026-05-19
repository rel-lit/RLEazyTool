"""解析器产出的指令类型（与具体处理逻辑解耦）。"""

from enum import StrEnum


class Action(StrEnum):
    MOD = "mod"
    QUIT = "quit"
    HELP = "help"
    HISTORY = "history"
    LIST_DIRS = "list_dirs"
    TOGGLE_MERGE_SCOPE = "toggle_merge_scope"
    CONTINUOUS_MODE = "continuous_mode"
    SWITCH_HISTORY = "switch_history"
    MERGE = "merge"
    SWITCH_ABS = "switch_abs"
    SWITCH_REL = "switch_rel"
    EXC_LAST = "exc_last"
    EXC_ADD = "exc_add"
    EXC_DEL = "exc_del"
    EXC_USE = "exc_use"
    EXC_DISABLE = "exc_disable"
    EXC_LIST = "exc_list"
    EXC_CASE = "exc_case"
    EXC_INVALID = "exc_invalid"
    CHOOSE = "choose"
    CHOOSE_INVALID = "choose_invalid"
    INVALID = "invalid"
