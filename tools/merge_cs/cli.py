# 命令行解析与交互相关代码

def parse_and_dispatch(user_input, context):
    """
    解析用户输入并分发命令。
    context: dict，包含 config, current_path, 其它状态。
    返回 (action, result) 元组。
    action: str，指令类型（如 'quit', 'help', 'merge', 'switch_path', 'invalid', ...）
    result: 相关数据或 None
    """
    user_input = user_input.strip()
    config = context['config']
    current_path = context['current_path']
    # Mod 指令
    if user_input.lower().startswith('mod '):
        parts = user_input.strip().split()
        return ('mod', parts)
    # 其它指令
    if user_input.lower() == 'q':
        return ('quit', None)
    if user_input.lower() == 'help':
        return ('help', None)
    if user_input.lower() == 'm':
        return ('history', None)
    if user_input.lower() == 'll':
        return ('list_dirs', None)
    if user_input.isdigit() and 1 <= int(user_input) <= len(config.get('history', [])):
        idx = int(user_input) - 1
        return ('switch_history', idx)
    if user_input == "":
        return ('merge', None)
    # 路径切换
    if user_input.startswith('"') and user_input.endswith('"'):
        user_input = user_input[1:-1]
    if ":" in user_input:
        return ('switch_abs', user_input)
    if user_input.startswith('\\') or user_input.startswith('/'):
        return ('switch_rel', user_input)
    # 无效指令
    return ('invalid', user_input)
