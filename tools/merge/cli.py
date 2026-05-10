# 命令行解析与交互相关代码


def _is_exc_command(user_input):
    """仅将 exc 子命令视为排除组指令，避免误匹配如 exceptions。"""
    s = user_input.strip().lower()
    return s == "exc" or s.startswith("exc ")


def parse_and_dispatch(user_input, context):
    """
    解析用户输入并分发命令。
    context: dict，包含 config, current_path, 其它状态。
    返回 (action, result) 元组。
    action: str，指令类型（如 'quit', 'help', 'merge', 'switch_path', 'invalid', ...）
    result: 相关数据或 None
    """
    user_input = user_input.strip()
    config = context["config"]
    # Mod 指令
    if user_input.lower().startswith("mod "):
        parts = user_input.strip().split()
        return ("mod", parts)
    # 其它指令
    if user_input.lower() == "q":
        return ("quit", None)
    if user_input.lower() == "help":
        return ("help", None)
    if user_input.lower() == "m":
        return ("history", None)
    if user_input.lower() == "ll":
        return ("list_dirs", None)
    if user_input.lower() == "this":
        return ("toggle_merge_scope", None)
    if user_input.lower() == "r":
        return ("continuous_mode", None)
    if user_input.isdigit() and 1 <= int(user_input) <= len(config.get("history", [])):
        idx = int(user_input) - 1
        return ("switch_history", idx)
    if user_input == "":
        return ("merge", None)
    # 路径切换
    if user_input.startswith('"') and user_input.endswith('"'):
        user_input = user_input[1:-1]
    if ":" in user_input:
        return ("switch_abs", user_input)
    if user_input.startswith("\\") or user_input.startswith("/"):
        return ("switch_rel", user_input)
    # exc 指令组
    if _is_exc_command(user_input):
        parts = user_input.strip().split()
        if len(parts) == 1:
            return ("exc_last", None)
        if len(parts) >= 3 and parts[1] == "a":
            group_name = parts[2]
            words = parts[3:]
            return ("exc_add", (group_name, words))
        if len(parts) == 3 and parts[1] == "d":
            group_name = parts[2]
            return ("exc_del", group_name)
        if len(parts) == 3 and parts[1] == "u":
            group_name = parts[2]
            return ("exc_use", group_name)
        if len(parts) == 2 and parts[1] == "q":  # exc q 指令
            return ("exc_disable", None)
        if len(parts) == 2 and parts[1] == "ll":
            return ("exc_list", None)
        if len(parts) == 4 and parts[1] == "case":
            group_name = parts[2]
            mode = parts[3]
            return ("exc_case", (group_name, mode))
        return ("exc_invalid", None)
    # 无效指令
    return ("invalid", user_input)
