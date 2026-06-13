# RLEazyTool

一些简易的便用小工具集合，提升日常开发效率。

## 📢 最新更新

- 🔧 **Merge**: `this` / `exc` / `c` / `ana`（tree-sitter 详细语法分析，默认关）、`.gitignore`
- 🆕 **factory-balance**: 异星工厂自平衡布局计算器（**v2 六阶段流水线** · SBTO · Vue 图形界面，含 Space Age；语义由 rellit 定稿）
- 🔧 **架构**: 分层模块（`session`、`scope_rules`、`exc_handlers` 等），详见 [tools/merge/README.md](tools/merge/README.md)
- 📝 **环境**: 虚拟环境支持（`.venv`）；merge 的 `.gitignore` 需可选依赖 `pathspec`

## 依赖与环境说明

### Python 版本
- Python 3.6 及以上（推荐 3.10+；当前 merge 工具在 3.10+ 下开发与测试）
- Windows 系统（部分功能依赖 Windows API）

### 虚拟环境（推荐）

项目已配置虚拟环境 `.venv`，使用虚拟环境可以：
- ✅ 隔离项目依赖，避免冲突
- ✅ 无需管理员权限安装包
- ✅ 方便分享和复现环境

**快速激活虚拟环境**：
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

详细虚拟环境设置指南请查看：[VENV_GUIDE.md](VENV_GUIDE.md)

### 核心库
- **merge 工具**: 合并扫描以标准库为主；**`.gitignore` / REPL 解析 / `ana` 详细分析** 由 `merge.bat` 或 `.venv` 自动准备（`requirements-core.txt`：pathspec、parsy、常用 grammar；`requirements-extra.txt` 按需）

## 目录结构

```
RLEazyTool/
├── .venv/                      # Python 虚拟环境（已忽略）
├── tools/
│   ├── merge/                  # 代码合并工具 → 完整说明见 README.md
│   │   ├── README.md           # merge 使用与架构说明
│   │   ├── main.py             # 入口
│   │   ├── repl.py             # 交互主循环
│   │   ├── input_parser.py     # 指令解析
│   │   ├── session.py          # 构建合并选项
│   │   ├── command_handlers.py # mod
│   │   ├── exc_handlers.py     # exc 排除模板
│   │   ├── exclude_rules.py    # 目录/文件名规则
│   │   ├── gitignore_support.py
│   │   ├── scope_handlers.py   # this 范围
│   │   ├── choose_handlers.py  # c 点名
│   │   ├── merge_engine.py     # 扫描与合并
│   │   ├── merge_report.py     # 报表与写盘
│   │   ├── requirements.txt    # 可选 pathspec
│   │   ├── merge.bat
│   │   └── test_*.py
│   └── factory-balance/        # 异星自平衡布局 → README.md
│       ├── balance.bat
│       ├── backend/
│       └── frontend/
├── .gitignore
├── README.md
└── VENV_GUIDE.md               # 虚拟环境设置指南
```

## 工具说明

### 1. merge —— 多类型代码合并工具

将指定目录下选定后缀的文件合并为一个文本文件，默认输出到桌面，并附带统计（默认粗略；`ana` 开时为 tree-sitter 符号分析）。

**典型使用场景：**
- 将大量源码合并为单文件，便于交给大模型分析或生成文档。
- 快速打包分享、归档与查阅。

#### 快速开始

1. 进入 `tools/merge/`，双击 **`merge.bat`**，或执行：`py main.py`
2. 按提示切换目录（绝对路径、`\\` 相对路径、历史记录 `1`–`9` 等），**回车**执行合并。
3. 桌面上生成：`<目录名>_MergedFiles_<时间戳>.txt`

若在 Windows 默认控制台遇到 emoji 编码报错，可先设置：`PYTHONIOENCODING=utf-8`。

**更完整的指令表、模块说明与测试方式**见：📖 **[tools/merge/README.md](tools/merge/README.md)**

#### 指令摘要

| 类别 | 说明 |
|------|------|
| 基础 | `help`、`q`、`m`、`1`–`9`、`ll`、`r`、回车合并 |
| 路径 | 绝对路径；`\\` 或 `/` 相对路径（末级可模糊） |
| 范围 **this** | 当前合并根：`this` 开关；`this 0` / `this N` / `this max`；`this ll` / `this a` / `this s` |
| 类型 **mod** | `mod a` / `mod u` / `mod ll` / `mod d` |
| 排除 **exc** | 全局模板：`exc` 开关 / `exc u <组名>`，`exc dir` / `exc f` / `exc gitignore` |
| 分析 **ana** | `ana` 开关详细 tree-sitter 符号分析（默认仅粗略统计） |
| 点名 **c** | `c` / `c ll` / `c 3 5` / `c all` / `c limit` |

完整指令表见 📖 **[tools/merge/README.md](tools/merge/README.md)**（含 `exc` / `this` / `c` 全表）。

#### 配置文件 `merge_config.json`

记录历史路径、类型组、排除组、`merge_max_depth`、`merge_scope_exclude` / `include`、`use_gitignore`、`c_limit` 等。示例：

```json
{
  "history": ["D:/project/src"],
  "type_groups": { "default": [".cs"] },
  "current_type_group": "default",
  "exclude_groups": {
    "dev": {
      "skip_dirs": ["bin", "obj"],
      "file_rules": [{ "kind": "contains", "pattern": "Generated" }]
    }
  },
  "current_exclude_group": "dev",
  "merge_max_depth": null,
  "use_gitignore": false,
  "detail_analysis": false,
  "c_limit": 50
}
```

#### 统计说明

合并结果文件头部与控制台会输出各类型文件数、行数；对 `.cs` 还会输出类/结构体/枚举/接口及方法、字段等**粗粒度**统计（基于正则，复杂语法可能有偏差，仅供参考）。

#### 性能说明

当前为整体读入后再写出，体量极大时内存占用会升高；可用 `this 0` / `this N` 控制深度，或用 `exc` / `.gitignore` 缩小范围。

单元测试：`tools/merge/test_merge_logic.py`、`test_path_utils.py`。

### 2. factory-balance —— 异星自平衡布局计算器

根据配方自动计算 **SBTO 自平衡传送带顺序** 与布局图（含 Space Age，中文 GUI）。v2 采用 **原始树 → 合并图 → layer/rank → SBTO → 渲染** 六阶段流水线，节点即物品名。

- 双击 `tools/factory-balance/balance.bat` 启动（首次自动创建 `tools/factory-balance/.venv`）
- 完整说明见 📖 **[tools/factory-balance/README.md](tools/factory-balance/README.md)** · 设计规范 **[PIPELINE_DESIGN_V2.md](tools/factory-balance/docs/PIPELINE_DESIGN_V2.md)**

## 贡献与反馈

如有建议或问题，欢迎 issue 或 PR。
如有新平台适配、单元测试补充、性能优化建议，欢迎贡献！

## 📚 相关文档

- [虚拟环境设置指南](VENV_GUIDE.md) - 详细的虚拟环境配置说明
- [merge 工具说明](tools/merge/README.md) - 代码合并工具（指令、架构、测试）
