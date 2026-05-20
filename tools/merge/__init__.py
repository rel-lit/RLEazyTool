"""
源码合并工具（交互式 CLI）。

分层说明:
  - ``models`` / ``storage``: 配置模型与 JSON 持久化
  - ``input_parser`` / ``actions``: 输入解析与指令枚举
  - ``command_handlers`` / ``path_switch``: 子命令与路径切换
  - ``session``: 从 REPL 构建合并选项
  - ``merge_engine`` / ``cs_analyzer``: 扫描与合并（无 print）
  - ``merge_report``: 报告生成、控制台汇总与写盘
  - ``repl``: 会话状态与主循环

入口: ``main.py`` 或 ``merge.bat``（在解压目录下运行）。
"""
