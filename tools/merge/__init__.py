"""
源码合并工具（交互式 CLI）。

分层说明:
  - ``models`` / ``storage``: 配置模型与 JSON 持久化
  - ``input_parser`` / ``actions``: 输入解析与指令枚举
  - ``command_handlers``: mod 子命令
  - ``exc_handlers`` / ``exclude_rules`` / ``gitignore_support``: 全局排除模板
  - ``scope_handlers`` / ``scope_rules``: this 目录范围
  - ``choose_handlers``: c 点名合并
  - ``session``: 从 REPL 构建 ``MergeRunOptions``
  - ``merge_engine`` / ``cs_analyzer``: 扫描与合并（无 print）
  - ``merge_report``: 报告生成、控制台汇总与写盘
  - ``path_switch`` / ``path_tools``: 路径切换
  - ``repl``: 会话状态与主循环

入口: ``main.py`` 或 ``merge.bat``（在 tools/merge 目录下运行）。
可选依赖: ``requirements.txt``（pathspec，用于 .gitignore）。
"""
