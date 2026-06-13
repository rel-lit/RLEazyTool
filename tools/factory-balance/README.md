# 异星自平衡布局计算器 (factory-balance)

根据异星工厂（含 **Space Age**）配方，选择产出目标与供给模式，自动计算 **自平衡布局 (SBTO)** 与可视化有向图。

> **v2 流水线：** 原始树 → 合并图 → 层/秩 → SBTO → 渲染；节点即物品名，按需判断，六阶段严格隔离。详见 [`docs/PIPELINE_DESIGN_V2.md`](docs/PIPELINE_DESIGN_V2.md)。

## 存档进度与配方同步（v0.2）

工具会读取 `%APPDATA%\\Factorio` 下的存档，并通过 **companion 模组** 导出当前已研究科技与 `force.recipes` 中已启用配方（与游戏内可制造列表一致）。

### 流程

1. 在界面选择存档 → **读取存档并同步配方**
2. 工具将 `companion-mod/factory-balance-sync` 复制到 `mods/` 目录
3. 读取存档当前 **tick**，再用 `--load-game --until-tick 当前tick+N` 向前模拟，触发 companion 模组导出

> **不用** `--benchmark`（headless 下 companion 模组会崩溃）。
> **不用** 手动在游戏里配模组；工具会自动复制并启用 `factory-balance-sync`。
4. 可选：首次同时运行 `--dump-data` 刷新完整配方库与中文 locale
5. 产出列表勾选 **仅显示当前可制造产物**

### 环境要求

- 已安装 Factorio 2.0 + Space Age（与存档模组一致）
- 若未自动找到游戏，设置环境变量：`FACTORIO_EXE=C:\...\Factorio.exe`
- 或在本工具目录创建 `factorio.local.json`：`{"factorio_exe": "D:\\game store\\steamapps\\common\\Factorio\\bin\\x64\\Factorio.exe"}`
- 工具也会尝试从 `%APPDATA%\\Factorio\\factorio-current.log` 自动解析路径（Steam 非默认安装目录）
- 存档需能正常加载；若模组列表变更，请先在游戏中同步模组

### 手动导出（备选）

在游戏中加载存档后，控制台执行（无需 companion 模组时不可用 force.recipes 导出）——推荐使用工具内置流程。

## 功能概览

- 多产出目标（共享原料合并为 **物品节点图**）
- 供给模式：**原料模式 (RAW)** / **直接产物模式 (DIRECT)**
- **禁止供给**：仅阻止外源叶子；能展开则继续建树，**建树失败才报错**
- 自动计算共享传送带 **取用顺序 (SBTO)**（仅 layer↓ rank↓，无门控、无 detour）
- 图形化布局（Vue Flow）：节点 id = **物品名**；四类边 `belt` / `tap_chain` / `product` / `hidden`
- 中文界面
- **占位扩展**：蓝图导出、产能计算（未实现）

## 快速开始

### 1. Python 依赖（子工具独立虚拟环境）

本工具使用 **`tools/factory-balance/.venv`**，与项目根 `.venv`（merge）分离，**不会安装到全局 Python**。

```bash
# 方式 A：一键初始化
tools\factory-balance\setup.bat

# 方式 B：手动
cd tools\factory-balance
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`balance.bat` 首次运行也会自动创建 `.venv` 并安装依赖。

Windows 控制台若中文乱码，脚本已自动 `chcp 65001`；在 Cursor/PowerShell 中手动运行时请设：`$env:PYTHONIOENCODING='utf-8'`。

### 2. 前端构建（首次）

```bash
cd tools\factory-balance\frontend
npm install
npm run build
```

### 3. 启动

双击 `tools\factory-balance\balance.bat`，或：

```bash
cd tools\factory-balance\backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8765
```

浏览器打开 http://127.0.0.1:8765

### 开发模式

- 后端：`uvicorn main:app --reload --port 8765`（在 `backend/` 目录）
- 前端：`npm run dev`（在 `frontend/`，代理 `/api` → 8765）

## 布局流水线（v2）

完整设计规范见 **[`docs/PIPELINE_DESIGN_V2.md`](docs/PIPELINE_DESIGN_V2.md)**。静态 Tag / 数据源 D 定义见 **[`backend/db/ANALYSIS_SUPPLY_SEMANTICS.md`](backend/db/ANALYSIS_SUPPLY_SEMANTICS.md)**。

```
用户输入 + 配方库 + 数据源 D
  → 1. recipe_pick + original_tree（双指针建树，analysis_items 注册）
  → 2–3. layer（叶=0 向终端递增）+ 跨树合并 → 原始图 G
  → 4. rank（L0 分数 × 子 rank 乘积 → 层内整型）
  → 5. SBTO（生产者侧发现；tap = layer↓ rank↓）
  → 6. render（坐标 + product / belt / hidden / tap_chain 四类边）
```

| 原则 | 说明 |
|------|------|
| **节点 = 物品名** | 合并后每个物品一个节点；`type=item` |
| **分析集** | 物品加入原始树时 `set.add`；非旧版闭包即时失败 |
| **禁止供给** | 叶子决策：能展开则继续；仅无法建树时标记 `impossible` |
| **SBTO 时机** | **必须在** 原始图 G 与 layer/rank 就绪 **之后** |
| **无 detour** | 几何曲线仅为渲染；算法无绕行语义 |

布局快照按 `layout_key` upsert 至 SQLite 表 `layout_snapshot`（算法 response + 用户坐标），可在侧栏 **历史** 中载入。

## 目录结构

```
factory-balance/
├── balance.bat
├── setup.bat
├── docs/
│   └── PIPELINE_DESIGN_V2.md     # v2 全流程设计规范
├── backend/
│   ├── main.py                   # FastAPI
│   ├── api/
│   ├── core/
│   │   ├── layout_pipeline.py    # 阶段 1→6 串联
│   │   ├── layout_engine.py      # API 入口 compute_layout
│   │   ├── original_tree.py      # 阶段 1：双指针原始树
│   │   ├── original_graph.py     # 原始图 G 数据结构
│   │   ├── tree_layer.py         # 阶段 2–3：layer + 合并
│   │   ├── rank_assigner.py      # 阶段 4：rank
│   │   ├── recipe_pick.py        # 多 primary 配方优化
│   │   ├── sbto.py               # 阶段 5：SBTO
│   │   ├── layout_renderer.py    # 阶段 6：渲染
│   │   ├── layout_geometry.py    # 坐标与 cross 布局
│   │   ├── blueprint.py          # 占位
│   │   └── throughput.py           # 占位
│   └── db/
│       ├── ANALYSIS_SUPPLY_SEMANTICS.md
│       └── ...
├── frontend/                     # Vue 3 + Vue Flow
│   └── src/layout/focus/         # 画布 focus 状态机
└── tests/
    ├── test_pipeline_v2.py
    └── test_v2_layer_rank.py
```

## 测试

在 `tools/factory-balance` 目录，使用子工具 venv：

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 后续版本（占位）

- **阶段二**：产能 / 装配机数量（`throughput.py`）
- **阶段三**：Factorio 蓝图导出（`blueprint.py`）
- 从游戏目录加载完整配方 / 模组
