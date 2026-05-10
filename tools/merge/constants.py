"""合并扫描常量。"""

# 递归遍历时跳过的目录名（与构建产物 / VCS 相关）
EXCLUDE_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        "bin",
        "obj",
        "node_modules",
        ".vs",
        "packages",
        "Debug",
        "Release",
    }
)
