# 布局检视域 — 正式版 V1

> **状态：** 已实现（frontend `domains/layout-inspection` + 关联编排）。  
> **关联：** UI 接线见 `UI_INTERACTION.md` §13；布局计算与 `recipe_details` 见 `PIPELINE_DESIGN_V2.md` 阶段 6 分析元数据。

---

## 1. 目标

用户在画布上 **hover / 钉选** 节点或边时：

1. 画布高亮（dim / focus）与 **检视选中** 分离；
2. 列表 chip 显示 **layout-mark**（布局 tier 空心环）与 **canvas-focus**（淡绿虚线沿圈流动），两模块零交叉；
3. 信息栏「检视详情」按 **节点 / 边 / SBTO边** 三种语义展示，配方来自 **原始树 `recipe_assignments` 展开**；
4. 列表勾选、排序 **不打断** 画布检视（pin / 虚线框）。

---

## 2. 架构

```
layout-inspection（会话）
  ├─ pin / hover → FocusHighlight → 画布 dim（layout/focus/*）
  ├─ inspectionTarget → panelModel（节点 | 边，互斥）
  ├─ focusView（只读）→ item-list 圈选（ListChipShell）
  └─ clear() ← 重算开始 / 失败 / 进度重置 / 历史载入（不含列表勾选）

layout-analysis（只读）
  └─ recipe_assignments + recipe_details（计算时 DB 展开）

list-layout-mark
  └─ 镂空环；nodeRingRole 供检视「类型」标签

item-list / listFocusRing
  └─ hasListFocusRing(item, focusView)

app/wire + actions
  └─ 纯编排；SelectionChanged 仅 layout.invalidate，不清 inspection
```

### 2.1 关键路径

| 路径 | 职责 |
|------|------|
| `domains/layout-inspection/createLayoutInspection.ts` | 会话：pin、`inspectionTarget`、`panelModel`、`focusView`、`requestRef` |
| `domains/layout-inspection/focusProjection.ts` | 钉选 highlight → `LayoutFocusView` |
| `domains/layout-inspection/resolveInspectionPanel.ts` | 三种检视文本模型 |
| `domains/layout-inspection/flowEdgeKind.ts` | 边输送介质：传送带 / 管道 |
| `domains/list-layout-mark/nodeRingRole.ts` | 节点类型 ↔ 镂空环 rim |
| `components/item-list/ListChipShell.vue` | 列表圈选 SVG（SBTO 式 dashoffset 流动） |
| `layout/useLayoutCanvasRegion.ts` | 注入 inspection.pin |
| `app/wire/wireLayout.ts` | 生命周期 clear / invalidate |

---

## 3. 交互语义

| 动作 | 行为 |
|------|------|
| hover 节点/边 | 仅画布高亮，不改信息栏选中 |
| click 节点/边 | pin + `inspectionTarget`；**不**自动展开信息栏（仅显示拉手） |
| click 空白 | 清除 pin 与检视 |
| 列表点 chip | 更新 selection；**不清除** pin / 虚线框 |
| 重算布局 | `layoutInspection.clear()` |
| 列表排序 commit | 虚线框按 **物品名** 跟随 chip（`:key="item.name"`） |

---

## 4. 信息栏文本格式（V1）

**全局**

- **标题 `title`**：仅中文标签；节点 = 物品名；边 = `上游 → 下游`。
- **徽章 `badge`**（副标题区）：`节点` | `边` | `SBTO边`；**永不显示内部 id**（如 `passive-provider-chest`）。
- **配方**：统一来自 `analysis.recipe_details`；范围 = 钉选 `focusView.itemNames`；按 layer 降序。

---

### 4.1 节点检视

```
检视详情
────────────────────────
被动供货箱（红箱）          ← title
节点                        ← badge

【基本信息】
  层级 layer 5
  类型 有效终端             ← nodeRingRole，对齐镂空环

【相关配方】                ← focusView = 依赖子树全部 item
  被动供货箱（红箱）：钢箱×1 + … → 被动供货箱（红箱）×1
  集成电路：…
  …
  原油：世界抽取 → 原油
  煤矿：世界开采 → 煤矿
  铁矿：世界开采 → 铁矿
```

**节点类型标签（与镂空环 rim 对应）**

| rim | 中文标签 |
|-----|----------|
| terminal | 有效终端 |
| demoted | 被降级声明终端 |
| intermediate | 中间产物 |
| extract | 抽取中间产物 |
| pure-solid | 外源（固体） |
| pure-world | 世界基准外源 |
| assumed | 假定外源 |
| forbidden | 禁止供给 |

---

### 4.2 普通边检视（belt）

```
检视详情
────────────────────────
塑料 → 集成电路              ← title
边                           ← badge

【基本信息】
  上游 塑料 · layer 3 · 中间产物
  下游 集成电路 · layer 4 · 有效终端
  层级跨度 layer 3 → 4
  输送介质 传送带              ← 或「管道」（流体物品）

【相关配方】                 ← focusView = {from, to}
  塑料：…
  集成电路：…
```

---

### 4.3 SBTO 边检视（tap_chain）

```
检视详情
────────────────────────
集成电路 → 电路板            ← title（本段）
SBTO边                       ← badge

【基本信息】
  共享物 铜缆
  本段 集成电路（layer 4）→ 电路板（layer 3）
  段序 第 2 段 / 共 3 段
  上游 中间产物 · 下游 中间产物

【SBTO 链详情】
  取用顺序 集成电路 → 电路板 → …
  共享物「铜缆」上，…（规则说明）

  涉及物品配方               ← 嵌在链详情内，非独立「配方」段
    集成电路：…
    电路板：…
    铜缆：…
```

---

## 5. 列表 UI

| 元素 | 层 | 说明 |
|------|-----|------|
| 镂空环 | `UiChip` + `list-layout-mark` | tier / 外源 / 禁止等 |
| 虚线圈选 | `ListChipShell` | 淡绿 SVG，`stroke-dashoffset` 流动（同 SBTO 边） |
| chip 尺寸 | 产出 / 供给统一 `size="sm"` | |

**CatalogPanel 必须声明 `resolveLayoutMark` prop**（否则产出列表镂空环恒为空）。

---

## 6. 后端：recipe_details

计算布局时在 `layout_pipeline` 调用 `build_recipe_details(recipe_assignments, db)`，写入 `analysis.recipe_details`：

```json
{
  "iron-plate": {
    "recipe_name": "iron-plate",
    "label": "铁板",
    "line": "铁矿×1 → 铁板×1",
    "kind": "craft"
  }
}
```

- `kind`: `craft` | `extract` | `world-supply` | `unknown`
- **extract**：闭包内展开的 `fb-extract:*` 配方（如原油）
- **world-supply**：分析集内外源 baseline 叶子（如铁矿/铜矿/煤），无 `recipe_assignments` 条目
- 旧快照无 `recipe_details` 时，前端按节点 `external_leaf` / `world_baseline` 回退「世界开采」

实现：`backend/core/recipe_display.py`。

---

## 7. 反模式（勿恢复）

- `useLayout.selectedEdgeId` / props 下发边选中
- 左侧固定「SBTO 取用顺序」全局面板
- click 检视自动 `openInfoToDefault()`
- `SelectionChanged` 时 `layoutInspection.clear()`
- 画布圈选画在 `UiChip` 内部（与 layout-mark 争 z-index）
- 信息栏副标题显示物品内部 id

---

## 8. 测试

```bash
# frontend
cd tools/factory-balance/frontend
npm run build
npx tsx tests/layout-inspection.test.ts
npx tsx tests/order-sort.test.ts

# backend
cd tools/factory-balance
python -m pytest tests/test_recipe_display.py -q
```
