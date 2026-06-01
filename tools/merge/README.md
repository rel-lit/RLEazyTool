# Merge 工具

将指定目录下的源码（可多后缀）合并成一个文本文件，默认输出到桌面，并附带统计（默认粗略；`ana` 开时为 tree-sitter 符号级分析）。

## 运行方式

在 `tools/merge` 目录下：

- 双击或在命令行执行 **`merge.bat`**
- 或执行：`py main.py`

建议在 **UTF-8 终端** 下使用（避免部分控制台 emoji 报编码错误）；必要时可设置环境变量：`PYTHONIOENCODING=utf-8`。

## 使用说明

启动后按提示输入指令；**直接回车** 对**当前路径**执行合并。

### 基础指令

| 指令 | 说明 |
|------|------|
| `help` | 显示完整指令说明（与下文结构一致） |
| `q` | 退出 |
| `m` | 显示历史路径 |
| `1`～`9` | 切换到对应序号的历史路径 |
| `ll` | 列出当前目录下的文件夹 |
| `r` | 持续合并模式（每次回车合并，用 `q` 退出程序） |
| 绝对路径（如 `D:\project\src`） | 切换当前目录 |
| `\相对路径` 或 `/相对路径` | 相对当前目录切换；最后一级支持模糊匹配 |
| 回车 | 执行合并（`c` 模式下仅合并已选文件） |

### 目录范围（this）

仅作用于**当前合并根目录**（你切换进去的路径），与 **mod**（后缀）、**exc**（全局排除）独立。配置写入 `merge_config.json`，退出 this 模式后合并不再应用范围，但深度与细则仍保留。

| 指令 | 说明 |
|------|------|
| `this` | 开关 **this 配置模式**（进入时启用已保存范围；退出后合并不再应用，设置仍保留） |
| `this 0` | 保存「仅本层」深度（深度 0；**仅 this 模式开启时**合并才生效） |
| `this N` | 保存最大深度 N（N≥1；**仅 this 模式开启时**合并才生效） |
| `this max` | 保存为不限深度 |
| `this ll` | 列出第 0 层文件夹（等同 `this ll 0`，带选中标记） |
| `this ll N` | 列出第 N 层文件夹（需已开启 this 配置模式） |
| `this ll all` | 列出整棵目录树可配置节点（需已开启 this 配置模式） |
| `this a <路径...>` | 添加细则包含（多级路径；需已开启 this 配置模式） |
| `this s` | 显示排除用法 |
| `this s <路径...>` | 排除子路径（不可排除顶层文件夹；需已开启 this 配置模式） |

### 类型组（mod）

| 指令 | 说明 |
|------|------|
| `mod a <组名> <后缀...>` | 新增类型组，如：`mod a web .cs .tsx` |
| `mod u <组名>` | 切换到该类型组 |
| `mod ll` | 列出所有类型组 |
| `mod ll now` | 查看当前组的后缀列表 |
| `mod d <组名>` | 删除类型组（`default` 不可删） |

### 排除模板（exc，全局）

与 **mod** 类似：排除组持久保存。`exc` 开关启用/关闭（恢复上次使用的组）；`exc u <组名>` 指定组（避免与 `exc a` / `exc ll` 等子命令冲突）。作用于**任意当前路径**（全局），与 **this**（当前目录范围）独立。

| 指令 | 说明 |
|------|------|
| `exc` | 开关排除（关闭后再开恢复 `last_exclude_group`） |
| `exc u <组名>` | 启用指定排除组 |
| `exc a <组名>` / `exc d <组名>` | 新建空组 / 删除组 |
| `exc ll` / `exc ll now` | 列出所有组 / 当前启用组详情 |

**跳过目录名**（树上任意层级，文件夹名匹配，不是路径）：

| 指令 | 说明 |
|------|------|
| `exc dir a <组名> <名...>` | 追加，如 `bin`、`obj` |
| `exc dir d <组名> <名...>` | 移除 |
| `exc dir clr <组名>` | 清空组内目录名（程序内置 bin/obj 等仍生效） |
| `exc dir ll <组名>` | 列出 |

**文件名规则**（仅文件名，不含路径；不区分大小写）：

| 指令 | 说明 |
|------|------|
| `exc f a <组名> <kind> <pattern>` | 添加规则 |
| `exc f d <组名> <序号...>` | 按序号删除（见 `exc f ll`） |
| `exc f d <组名> <kind> <pattern>` | 按类型+pattern 删除 |
| `exc f clr <组名>` / `exc f ll <组名>` | 清空 / 列出 |

`kind`：`contains` | `prefix` | `suffix` | `glob` | `regex`

**`.gitignore`（可选，需 pathspec）**：

| 指令 | 说明 |
|------|------|
| `exc gitignore on` / `exc gitignore off` | 按仓库 `.gitignore` 排除 |
| `exc gitignore` | 查看开关状态、各 `.gitignore` 文件规则明细 |

### 点名合并（c）

| 指令 | 说明 |
|------|------|
| `c` | 开关 c 模式（关闭时清空选择） |
| `c ll` | 列出 mod+exc 候选（带序号，需已开启 c 模式） |
| `c <编号...>` | 累加选择，如 `c 3 5 7` |
| `c s <编号...>` | 取消已选；单独 `c s` 显示用法 |
| `c all` / `c s all` | 全选 / 取消全选 |
| `c limit <N>` | 候选超过 N 个时不列出（仅 c 模式下，持久化，默认 50） |
| `c limit` | 查看当前 c limit（c 模式下） |

### 语法分析（ana）

| 指令 | 说明 |
|------|------|
| `ana` | 开关**详细语法分析**（默认关） |
| `ana show` | 查看当前模式与 tree-sitter 是否就绪 |

#### 粗略 vs 详细（默认粗略）

| | **粗略（默认，`ana` 关）** | **详细（`ana` 开）** |
|---|---------------------------|----------------------|
| 何时运行 | 每次合并自动 | 仅 `ana` 开启时 |
| 技术 | 读文件元数据，不解析语法 | tree-sitter 语法树 + 符号提取 |
| 合并头 | 行数、体积、按目录/后缀、文件清单 | 上述 **外加** 跨文件符号汇总、Top 符号跨度 |
| 每个源文件内 | 无分析块 | 符号 ≤80 个时插入 `// [分析] 路径` 与 L行号 列表 |
| 解析失败 | 不影响合并 | **正文仍合并**，仅无该文件/项目的分析节 |
| 依赖 | 无 | `.venv` 自动装（`requirements-core.txt` + `requirements-extra.txt`） |
| 适用 | 快速打包给 AI 阅读 | 需要类/方法/导入等 IDE 级结构概览 |

依赖分包：**core**（pathspec、parsy、C#/Py/JS/TS）在 gitignore 或首次需要时安装；**extra**（Go/Java/Rust 等）在分析对应后缀时按需安装。

## 合并时过滤顺序

```text
内置跳过目录 + exc.dir（全局）
  → walk 扫描
  → this（深度 + 目录路径细则）
  → mod（后缀）
  → exc.f（文件名规则）
  →（可选）.gitignore
  →（可选）c 点名
```

## 配置

- 配置文件：同目录下的 **`merge_config.json`**
- 会保存：历史路径、类型组、当前 mod、排除组、`merge_max_depth`、`merge_scope_*`、`use_gitignore`、`detail_analysis`、`c_limit` 等
- 旧版排除组里的 `words[]` 会在加载时自动迁成 `contains` 规则
- 首次运行或配置损坏时会使用默认值重建

### 推荐配置示例（可直接粘贴）

将下面整段保存为 **`tools/merge/merge_config.json`**（与 `merge.bat` 同目录；该文件通常已被 `.gitignore` 忽略，不会进仓库）。请先改 `history` 里的路径为你本机项目（最多保留 **9** 条，对应快捷键 `1`–`9`）；`current_*` 与 `merge_max_depth` 可按下表「常用场景」切换。程序已内置跳过 `bin`、`obj`、`.git` 等，`exc` 里可只写**额外**目录名。

```json
{
  "history": [
    "D:/Work/MyApp/src",
    "D:/Work/MyApp",
    "D:/Work/Frontend/packages/app"
  ],
  "type_groups": {
    "default": [".cs"],
    "csharp": [".cs", ".csproj", ".sln", ".props", ".targets"],
    "web": [".ts", ".tsx", ".js", ".jsx", ".vue", ".css", ".scss", ".html"],
    "python": [".py", ".pyi"],
    "go": [".go", ".mod", ".sum"],
    "java": [".java", ".kt", ".kts", ".gradle"],
    "docs": [".md", ".txt", ".rst"],
    "config": [".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".env.example"]
  },
  "current_type_group": "csharp",
  "last_success_type_group": "csharp",
  "exclude_groups": {
    "dotnet-dev": {
      "skip_dirs": [".idea", "TestResults", "artifacts"],
      "file_rules": [
        { "kind": "contains", "pattern": "Generated" },
        { "kind": "suffix", "pattern": ".Designer.cs" },
        { "kind": "suffix", "pattern": ".g.cs" },
        { "kind": "glob", "pattern": "*.AssemblyInfo.cs" }
      ]
    },
    "web-node": {
      "skip_dirs": ["dist", "build", ".next", ".nuxt", "coverage", ".turbo", "storybook-static"],
      "file_rules": [
        { "kind": "suffix", "pattern": ".min.js" },
        { "kind": "suffix", "pattern": ".min.css" },
        { "kind": "suffix", "pattern": ".map" },
        { "kind": "contains", "pattern": ".spec." },
        { "kind": "contains", "pattern": ".test." }
      ]
    },
    "unity": {
      "skip_dirs": ["Library", "Temp", "Logs", "obj", "Build", "Builds", "UserSettings"],
      "file_rules": [
        { "kind": "suffix", "pattern": ".meta" }
      ]
    },
    "python-venv": {
      "skip_dirs": [".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", "htmlcov"],
      "file_rules": [
        { "kind": "suffix", "pattern": ".pyc" }
      ]
    },
    "java-android": {
      "skip_dirs": [".gradle", "build", ".cxx", "captures", ".externalNativeBuild"],
      "file_rules": [
        { "kind": "suffix", "pattern": "R.java" },
        { "kind": "glob", "pattern": "BuildConfig.java" }
      ]
    },
    "minimal": {
      "skip_dirs": [],
      "file_rules": []
    }
  },
  "current_exclude_group": "dotnet-dev",
  "last_exclude_group": "dotnet-dev",
  "merge_max_depth": null,
  "merge_scope_exclude": [],
  "merge_scope_include": [],
  "scope_enabled": true,
  "c_limit": 50,
  "use_gitignore": false,
  "detail_analysis": false
}
```

**字段说明（与 REPL 对应）**

| 配置项 | 含义 | REPL 等价 |
|--------|------|-----------|
| `current_type_group` | 当前 mod 组 | `mod u <组名>` |
| `current_exclude_group` | 当前启用的 exc 组；`null` 表示关闭 | `exc` 开关 / `exc u <组名>` |
| `last_exclude_group` | 上次启用或合并成功的组，供 `exc` 开关恢复 | 启用组或合并成功时写入 |
| `merge_max_depth` | `null` 不限深度；`0` 仅本层；`N` 最多 N 层 | `this max` / `this 0` / `this N` |
| `merge_scope_include` / `exclude` | 相对当前合并根目录的路径细则 | `this` 模式下 `this a` / `this s` |
| `scope_enabled` | 合并时是否应用上述范围；退出 `this` 时为 `false` | 输入 `this` 进入配置模式为 `true` |
| `use_gitignore` | 是否按仓库 `.gitignore` 排除 | `exc gitignore on` / `off` |
| `detail_analysis` | 是否启用 tree-sitter 详细分析 | `ana` 开关 |
| `c_limit` | `c ll` 候选过多时的上限 | `c limit <N>` |

**常用场景：改哪几项**

| 场景 | `current_type_group` | `current_exclude_group` | `merge_max_depth` | `merge_scope_*` | `use_gitignore` |
|------|----------------------|---------------------------|-------------------|-----------------|-----------------|
| .NET 全项目合并 | `csharp` | `dotnet-dev` | `null` | 空 | `true`（需安装 pathspec） |
| 只合并 `src` 下、跳过测试目录 | `csharp` | `dotnet-dev` | `null` | `include`: `["src"]`，`exclude`: `["Tests"]` | 按需 |
| 仅当前文件夹一层 `.cs` | `default` | `dotnet-dev` | `0` | 空 | `false` |
| 向下最多 2 层 | `csharp` | `dotnet-dev` | `2` | 空 | `false` |
| React/Vue 前端 | `web` | `web-node` | `null` | 空 | `true` |
| Unity 脚本（少扫资源） | `default` | `unity` | `null` | 空 | `false` |
| Python 项目 | `python` | `python-venv` | `null` | 空 | `true` |
| Java / Kotlin（含 Android） | `java` | `java-android` | `null` | 空 | `true` |
| 文档与说明 | `docs` | `minimal` 或 `null` | `0` 或 `null` | 空 | `false` |
| 尽量全收、少过滤 | 任选 | `minimal` 或 `null` | `null` | 空 | `false` |

**带目录细则的片段示例**（合并根为 `D:/Work/MyApp` 时，只关心 `src` 且排除 `src/Legacy`）：

```json
"merge_max_depth": null,
"merge_scope_include": ["src"],
"merge_scope_exclude": ["src/Legacy"]
```

路径一律用 **`/`** 分隔、不带首尾斜杠，与 `this ll` 里显示的一致。修改 JSON 后**重新启动** merge，或在 REPL 里用对应 `mod` / `exc` / `this` 命令覆盖当前会话。

## 代码结构（便于二次开发）

| 模块 | 职责 |
|------|------|
| `main.py` | 入口，转调 `repl` |
| `repl.py` | 交互主循环、会话状态 |
| `session.py` | 从配置/REPL 构建 `MergeRunOptions` 与过滤器 |
| `input_parser.py` / `repl_command_parser.py` / `actions.py` | parsy 组合子解析指令 |
| `command_handlers.py` | `mod` 命令 |
| `exc_handlers.py` | `exc` 排除模板 |
| `exclude_rules.py` | 目录跳过与文件名规则匹配 |
| `gitignore_support.py` | `.gitignore` 解析（依赖 pathspec） |
| `choose_handlers.py` / `scope_handlers.py` | `c` / `this` 模式 |
| `scope_rules.py` | 深度与目录细则（`ScopeContext`） |
| `path_switch.py` / `path_tools.py` | 路径切换与桌面、模糊匹配 |
| `models.py` / `storage.py` | 配置、选项、结果模型与 JSON |
| `merge_engine.py` | 扫描与合并（无控制台输出） |
| `file_analysis.py` | 粗略统计（行数、目录、清单） |
| `analysis/` | tree-sitter 详细语法分析（`ana` 开时） |
| `analyze_handlers.py` | `ana` 开关 |
| `merge_report.py` | 报告行生成、终端摘要与写盘 |
| `constants.py` | 递归遍历时跳过的目录名 |

## .gitignore 兼容（可选）

在项目根 **`.venv`** 中安装依赖（勿全局 `pip install`），推荐直接双击 **`merge.bat`**（会自动使用 `.venv` 里的 Python）：

```text
cd <项目根>
python -m venv .venv
.venv\Scripts\activate
pip install -r tools\merge\requirements.txt
```

```text
exc gitignore on
exc gitignore    # 列出各 .gitignore 文件与规则明细
```

合并与 `c ll` 扫描均会跳过被 ignore 的路径。需在 Git 仓库内（当前路径向上能找到 `.git`）。与 **this**（当前目录范围）独立。

## 测试

在 `tools/merge` 下：

```text
pip install -r requirements.txt
py test_merge_logic.py
py test_path_utils.py
```

若控制台编码异常，可先设置 `PYTHONIOENCODING=utf-8` 再运行。

## 输出文件

- 默认保存在 **桌面**，文件名形如：`<文件夹名>_MergedFiles_<时间戳>.txt`
- 文件开头为统计注释块（合并时间、路径、范围、文件数、按后缀/目录分析、文件清单与 Top 排行；`ana` 开时另有 tree-sitter 符号汇总），其后为各文件内容区块（详细模式下可有 `// [分析]` 块）。
- 终端仅输出简短摘要（行数 Top5；`ana` 开时为符号条数与 Top3，不刷 `//` 注释行）；完整 `// --- 详细语法分析 ---` 与 `// --- 文件体量与清单 ---` 见输出文件头部。
