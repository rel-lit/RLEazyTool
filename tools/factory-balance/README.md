# 异星自平衡布局计算器 (factory-balance)

根据异星工厂（含 **Space Age**）配方，选择产出目标与供给模式，自动计算 **自平衡布局 (SBTO)** 与可视化有向图。

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

## 功能（v0.1）

- 多产出目标（合并共享生产链）
- 供给模式：**原料模式** / **直接产物模式**
- 自动计算共享传送带 **取用顺序 (SBTO)**
- 图形化布局（Vue Flow）
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

完整设计见 [`docs/PIPELINE_DESIGN_V2.md`](docs/PIPELINE_DESIGN_V2.md)：

1. 原始树构建 + 分析集  
2. layer（叶=0 向终端递增）+ 树合并  
3. rank（L0 分数 × 子节点乘积 → 层内整型）  
4. SBTO（仅 layer/rank，下游优先）  
5. 渲染（节点 id = 物品名，四类边通道）

## SBTO 规则

单次布局计算会先构建 **合并产物图** 并分配 **等级（layer）**，再在同一等级体系上计算 SBTO：

| 原则 | 说明 |
|------|------|
| **合并等级** | 多目标原始树合并后，节点取各路径 **max 等级**；越靠近有效终端越高 |
| **取用顺序** | 共享物上，**层级更高**（更下游）的消费者优先 tap；同层 **rank 更大** 者优先 |

每次成功计算会写入 SQLite 表 `layout_compute_history`（完整请求/响应 JSON），可在侧栏 **历史** 中载入。

## 目录结构

```
factory-balance/
├── balance.bat
├── setup.bat               # 初始化子工具 .venv
├── venv_bootstrap.py
├── .venv/                  # 子工具专用（git 忽略）
├── requirements.txt
├── backend/
│   ├── main.py              # FastAPI
│   ├── api/
│   ├── core/
│   │   ├── sbto.py          # SBTO 算法
│   │   ├── layout_engine.py
│   │   ├── blueprint.py     # 占位
│   │   └── throughput.py    # 占位
│   └── data/recipes.json    # vanilla + Space Age 配方快照
├── frontend/                # Vue 3 + Vue Flow
└── tests/
```

## 测试

在 `tools/factory-balance` 目录，使用子工具 venv：

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 后续版本（占位）

- **Phase 2**：产能 / 装配机数量（`throughput.py`）
- **Phase 3**：Factorio 蓝图导出（`blueprint.py`）
- 从游戏目录加载完整配方 / 模组
