# UI 交互基座方案（v1）

> 目标：为 factory-balance 前端**全部可点击控件**提供一致的悬停 / 焦点 / 按下 / 禁用反馈，**不**重构 domain、EventBus 或 App 业务编排。
>
> 风格：延续现有 GitHub 暗色主题；变化应 **subtle 但可感知**（用户能确认指针已在控件上）。

---

## 1. 范围

### 1.1 纳入（必须有完整交互态）

| 控件 | 现位置 | 目标 variant |
|------|--------|--------------|
| 计算自平衡布局 | `LayoutWorkspace` | `primary` |
| 从存档导入、清理过时缓存 | `ProgressPanel` | `secondary` |
| 刷新列表、清空全部 | `HistoryPanel` | `secondary` / `danger` |
| 历史条目「载入」「删除」 | `HistoryPanel` | `link` / `link-muted` |
| 存档 / 历史切换 | `App.vue` | `toggle` |
| 数据源、供给模式 | `ModeToolbar` | `toggle` |
| 产出目标 / 已知外部供给 tab | `ItemTabsPanel` | `tab`（已有 hover，迁入基座统一） |
| 搜索框内 × | `ItemTabsPanel` | `icon-button` |
| 清空当前选择 | `ItemTabsPanel` | `danger-soft` |
| 产出目标 chip | `CatalogPanel` | `chip` |
| 供给 chip（已知 / 禁止） | `SupplyPanel` | `chip` / `chip-forbidden` |

### 1.2 纳入（表单类，仅 hover + focus）

| 控件 | 现位置 |
|------|--------|
| 存档 `<select>` | `ProgressPanel` |
| 搜索 `<input>` | `ItemTabsPanel` |

### 1.3 不纳入本次

- 画布内 VueFlow 节点/边（另有 focus 高亮体系）
- domain / API / Layer P 逻辑
- App.vue 布局结构重组（独立后续任务）
- 移动端适配、动画库、第三方组件库

---

## 2. 目录结构（新增）

```
frontend/src/ui/
  tokens.css           # CSS 变量：色、边框、圆角、过渡
  interactive.css      # 交互态 mixin 等价物（普通 class 组合）
  UiButton.vue         # 块级/行内按钮
  UiChip.vue           # 物品 pill
  UiIconButton.vue     # 小圆形 × 等
  UiTabButton.vue      # 标签页按钮（可选，或 UiButton variant=tab）
  index.ts             # 统一 export
```

全局入口 `main.ts` 引入：

```ts
import "./ui/tokens.css";
import "./ui/interactive.css";
```

**原则**：panel 逐步改为使用 `Ui*` 组件；过渡期允许 `<button class="ui-btn ui-btn--secondary">` 纯 class 写法，避免半迁移状态长期并存。

---

## 3. Design Tokens

在 `tokens.css` 的 `:root` 定义：

```css
:root {
  /* 表面 */
  --ui-bg-app: #0f1419;
  --ui-bg-panel: #161b22;
  --ui-bg-inset: #0d1117;
  --ui-bg-control: #21262d;
  --ui-bg-control-hover: #30363d;
  --ui-bg-control-active: #282e36;

  /* 边框 */
  --ui-border: #30363d;
  --ui-border-muted: #21262d;
  --ui-border-accent: #388bfd;
  --ui-border-danger: #da3633;
  --ui-border-danger-soft: #6b4548;

  /* 文字 */
  --ui-text: #e6edf3;
  --ui-text-muted: #8b949e;
  --ui-text-accent: #58a6ff;
  --ui-text-danger: #f85149;
  --ui-text-danger-soft: #ddb8b8;
  --ui-text-on-primary: #ffffff;

  /* 强调面 */
  --ui-primary: #238636;
  --ui-primary-hover: #2ea043;
  --ui-primary-active: #196c2e;

  --ui-accent-bg: #1f3d5c;
  --ui-accent-bg-hover: #244a6e;

  --ui-danger-soft-bg: #3a2829;
  --ui-danger-soft-bg-hover: #452f31;

  --ui-chip-on-bg: #1f6feb;
  --ui-chip-on-bg-hover: #388bfd;
  --ui-chip-forbidden-bg: #3d1214;
  --ui-chip-forbidden-bg-hover: #4a181b;

  /* 几何 */
  --ui-radius: 6px;
  --ui-radius-pill: 999px;
  --ui-radius-icon: 50%;

  /* 动效 */
  --ui-transition: 0.15s ease;

  /* 焦点环 */
  --ui-focus-ring: 2px solid #388bfd;
  --ui-focus-offset: 2px;

  /* 禁用 */
  --ui-disabled-opacity: 0.5;
}
```

---

## 4. 交互态定义（全控件通用）

每个可点击控件必须实现 **五态**（无某态则标注 N/A）：

| 态 | 用户感知 | CSS 要点 |
|----|----------|----------|
| **default** | 可点击 | 基色来自 variant |
| **:hover** | 指针已在控件上 | 背景/边框/字色向 accent 或更亮偏移；`transition` |
| **:focus-visible** | 键盘 Tab 聚焦 | `outline: var(--ui-focus-ring); outline-offset: var(--ui-focus-offset)`；**不用** `:focus` 裸写，避免鼠标点击出现环 |
| **:active** | 按下瞬间 | 背景再暗一档（`--ui-bg-control-active` 或 variant active 色） |
| **:disabled** | 不可点 | `opacity: var(--ui-disabled-opacity); cursor: not-allowed`；**suppress** hover/active |

**禁止**：仅依赖 `cursor: pointer` 而无视觉变化。

**链接型按钮**（历史「载入」「删除」）：hover 下划线或字色加深，active 略回退。

---

## 5. Variant 规格表

### 5.1 `primary` — 主操作（计算布局）

| 态 | 背景 | 边框 | 文字 |
|----|------|------|------|
| default | `#238636` | none | `#fff` |
| hover | `#2ea043` | none | `#fff` |
| active | `#196c2e` | none | `#fff` |
| disabled | 同上 + opacity 0.6 | — | — |

用途：`LayoutWorkspace`「计算自平衡布局」。

---

### 5.2 `secondary` — 次要块级按钮

| 态 | 背景 | 边框 | 文字 |
|----|------|------|------|
| default | `#21262d` | `#388bfd` | `#58a6ff` |
| hover | `#30363d` | `#58a6ff` | `#79c0ff` |
| active | `#282e36` | `#388bfd` | `#58a6ff` |
| disabled | — | — | opacity 0.5 |

用途：导入、清缓存、刷新列表。  
`width: 100%` 由 panel 布局 class 控制，不进 variant 本身。

---

### 5.3 `danger` — 破坏性块级

| 态 | 背景 | 边框 | 文字 |
|----|------|------|------|
| default | `#21262d` | `#da3633` | `#f85149` |
| hover | `#3d1214` | `#f85149` | `#ffb4b4` |
| active | `#2d0e10` | `#da3633` | `#f85149` |

用途：History「清空全部」。

---

### 5.4 `danger-soft` — 软destructive（马卡龙红，已有）

| 态 | 背景 | 边框 | 文字 |
|----|------|------|------|
| default | `#3a2829` | `#6b4548` | `#ddb8b8` |
| hover | `#452f31` | `#805055` | `#eccaca` |
| active | `#322426` | `#6b4548` | `#ddb8b8` |
| disabled | `#21262d` | `#30363d` | `#8b949e` opacity 0.55 |

用途：ItemTabs「清空当前选择」。

---

### 5.5 `toggle` — 互斥选项（未选中 / 选中）

**未选中 (off)**

| 态 | 背景 | 边框 | 文字 |
|----|------|------|------|
| default | `#21262d` | `#30363d` | `#8b949e` |
| hover | `#30363d` | `#484f58` | `#c9d1d9` |
| active | `#282e36` | `#30363d` | `#8b949e` |

**选中 (on)** — 加 class `ui-btn--on`

| 态 | 背景 | 边框 | 文字 |
|----|------|------|------|
| default | `#1f3d5c` | `#388bfd` | `#58a6ff` |
| hover | `#244a6e` | `#58a6ff` | `#79c0ff` |
| active | `#1a3350` | `#388bfd` | `#58a6ff` |

用途：App 存档/历史、ModeToolbar 数据源与供给模式。  
`disabled` 时 suppress hover（catalog 加载中）。

---

### 5.6 `tab` — 标签页

| 态 | 背景 | 底边 | 文字 |
|----|------|------|------|
| default | transparent | 2px transparent | `#8b949e` |
| hover | transparent | 2px transparent | `#c9d1d9` |
| active tab | transparent | 2px `#388bfd` | `#58a6ff` |

用途：ItemTabs 产出目标 / 已知外部供给。

---

### 5.7 `chip` — 物品 pill

**未选中**

| 态 | 背景 | 边框 | 文字 |
|----|------|------|------|
| default | `#21262d` | `#30363d` | inherit |
| hover | `#30363d` | `#484f58` | `#e6edf3` |
| active | `#282e36` | `#30363d` | inherit |

**选中 `ui-chip--on`**

| 态 | 背景 | 边框 |
|----|------|------|
| default | `#1f6feb` | `#388bfd` |
| hover | `#388bfd` | `#58a6ff` |
| active | `#1a5fdb` | `#388bfd` |

**禁止供给 `ui-chip--forbidden`**

| 态 | 背景 | 边框 | 文字 |
|----|------|------|------|
| default | `#3d1214` | `#f85149` | `#ffb4b4` + line-through |
| hover | `#4a181b` | `#ff7b72` | `#ffc1c1` |

尺寸：`CatalogPanel` 12px；`SupplyPanel` 11px → prop `size="sm"|"md"`。

---

### 5.8 `link` / `link-muted`

| variant | default 字色 | hover |
|---------|-------------|-------|
| link | `#58a6ff` | `#79c0ff` + optional underline |
| link-muted | `#8b949e` | `#c9d1d9` |

背景 none，padding 0。用途：History 条目操作。

---

### 5.9 `icon-button`

16×16 圆，`#30363d` 底；hover `#484f58`；active `#21262d`。  
用途：搜索 ×（已有，迁入 UiIconButton）。

---

### 5.10 表单控件 `ui-input` / `ui-select`

| 态 | 边框 | 背景 |
|----|------|------|
| default | `#30363d` | `#0d1117` |
| hover | `#484f58` | `#0d1117` |
| focus-visible | `#388bfd` | `#0d1117` |

---

## 6. 组件 API 草案

### UiButton

```vue
<UiButton variant="primary" :disabled="loading" block>
  计算自平衡布局
</UiButton>

<UiButton variant="toggle" :pressed="catalogMode === 'progress'" @click="...">
  仅当前进度
</UiButton>
```

| Prop | 类型 | 说明 |
|------|------|------|
| `variant` | 见 §5 | 必填 |
| `pressed` | boolean | toggle/tab 选中态 |
| `disabled` | boolean | |
| `block` | boolean | width 100% |
| `size` | `'sm' \| 'md'` | default md |

默认 `type="button"`。支持默认 slot。

### UiChip

```vue
<UiChip :selected="selectedTargets.includes(item.name)" @primary="toggle">
  {{ item.label }}
</UiChip>

<UiChip variant="forbidden" :selected="..." @primary @secondary />
```

### UiIconButton

```vue
<UiIconButton aria-label="清空搜索" @primary="onClear">×</UiIconButton>
```

---

## 7. 迁移清单与顺序

按 **风险低 → 触达广** 分 PR，每步完成后全站点击 smoke test。

| 阶段 | 文件 | 动作 |
|------|------|------|
| **0** | `ui/*`, `main.ts` | 落地 token + 组件骨架 |
| **1** | `LayoutWorkspace.vue` | `primary` |
| **2** | `ProgressPanel.vue` | `secondary` ×2 + `ui-select` |
| **3** | `HistoryPanel.vue` | `secondary`, `danger`, `link` |
| **4** | `App.vue` | `toggle` ×2 |
| **5** | `ModeToolbar.vue` | `toggle` ×4 |
| **6** | `CatalogPanel.vue`, `SupplyPanel.vue` | `UiChip` |
| **7** | `ItemTabsPanel.vue` | 删本地 tab/clear/search-clear 样式，改用 Ui* |
| **8** | 扫尾 | 删 panel 内重复 `.primary`/`.secondary`/`.chip` scoped 规则 |

**不要**在阶段 0–8 之间改 `useApp` / domain / EventBus。

---

## 8. 验收标准

1. 上表 **§1.1 每一类控件** 在 `:hover` 时有可辨视觉变化（录屏或目视 checklist）。
2. 键盘 Tab 可达按钮均有 `:focus-visible` 环。
3. `disabled` 按钮 hover 无变化。
4. toggle 选中/未选中 **hover 变化不同** 但同一套逻辑。
5. chip 三种态（off / on / forbidden）hover 互不串色。
6. 无 panel 内遗留与 ui 基座冲突的旧 button 规则（grep `.primary{` 等应为 0，除 ui 目录外）。
7. `npm run build` 通过；无 layout/domain 行为变更。

---

## 9. 与「UI 架构重组」的边界

| 本方案（UI Interaction v1） | 未来可选（UI Shell v2） |
|----------------------------|-------------------------|
| tokens + UiButton/Chip | LeftSidebar 容器组件 |
| 统一 hover/focus | App.vue wiring composable |
| panel 替换 class | 概念文案 / 通知系统统一 |
| **不动** domain | supplyMode 收进 selection API |

完成 v1 后，用户可感知「所有按钮都有反馈」；架构债（App 胶水、EventBus 双轨）仍可按优先级单独排期。

---

## 10. 参考：现网缺失 hover 的控件（实施前基线）

- [x] `LayoutWorkspace` `.primary`
- [x] `ProgressPanel` `.secondary` ×2
- [x] `HistoryPanel` `.secondary`, `.link`
- [x] `ModeToolbar` `.sub-btn`
- [x] `CatalogPanel` / `SupplyPanel` `.chip`
- [x] `App.vue` `.toggle-save`
- [x] `ItemTabsPanel` tab / clear / search-clear

**实现目录**：`frontend/src/ui/`（`tokens.css`、`interactive.css`、`UiButton`、`UiChip`、`UiIconButton`）。

---

## 11. 物品列表：会话式展示与区外提交

> 参考商业化 headless 组件的分层方式（Radix `DismissableLayer` / `onPointerDownOutside`、Material roving tabindex、Ariakit Composite），**不把 focusout、relatedTarget、pointerleave 混进展示逻辑**。

### 11.1 模块边界

| 层 | 路径 | 职责 |
|----|------|------|
| 纯排序 | `domains/item-list/order.ts` | 桶内 `label → name` 字典序、flatten |
| 编辑会话 | `domains/item-list/session.ts` | 桶数组、`displayOrder` 冻结列、`dirty` 标记 |
| 区外提交 | `ui/interaction/useRegionOutside.ts`（VueUse `onClickOutside`） | `ItemTabsPanel` 编排调用 |
| 选择（业务） | `domains/selection/useSelection.ts` | `selectedTargets` / `suppliedItems` / `forbiddenItems` |
| 编排 | `components/panels/ItemTabsPanel.vue` | toggle → selection + session；**单例**区外提交 |
| dumb 渲染 | `CatalogPanel` / `SupplyPanel` | 只读 `displayOrder`；chip 用 `@primary` / `@secondary` |
| 视口壳 | `components/item-list/ItemListViewport.vue` | `useScrollRegion`（滚动 + 抑制空白区右键） |

### 11.2 交互语义

1. **列表内点击 chip**：只更新 selection（业务）+ 桶归属（session）；`displayOrder` **不变**；chip 高亮即时变化。
2. **区外 pointerdown**（搜索框、tab、清空、画布等）：对**当前 tab** 的 session 调用 `commit()`（仅 `dirty` 时重排）。
3. **commit 后分组**：产出目标 `[已选 → 未选]`；供给 `[已知 → 禁止 → 普通]`；组内字典序。
4. **取消选择**：桶回到 normal；下次 commit 时回到 normal 组位置。

### 11.3 反模式（旧设计，已废弃）

- 每个 `ItemListRegion` 各自挂 document listener → inactive tab 误 commit
- `focusout` + `relatedTarget` 判断离开
- 从 buckets 实时 flatten 渲染（应使用冻结的 `displayOrder`）
- 在 presentation 模块内耦合 `mode: catalog | grouped` 与焦点启发式

---

## 12. 交互语义层（v2 · UiControl + VueUse）

> Vue 3 无内置 Press/Hover 抽象。**唯一交互入口**为 `ui/primitives/UiControl.vue`；`UiButton` / `UiChip` / `UiIconButton` 仅为样式变体。  
> 底层依赖 [`@vueuse/core`](https://vueuse.org/)，业务 **只订阅语义 emit**（`@primary` / `@secondary` 等），禁止在 panel 绑 raw `@click` / `@contextmenu`。

### 12.1 目录

```
ui/
  primitives/UiControl.vue       # 唯一 <button> + 全量交互 wiring
  UiButton.vue / UiChip.vue / UiIconButton.vue   # 样式壳，inheritAttrs → UiControl
  interaction/
    useInteractiveTarget.ts      # VueUse：hover / press / focus / longPress / wheel / aux
    useUiControl.ts              # primary(click) + secondary(contextmenu) → emit
    useRegionOutside.ts          # onClickOutside（列表 commit、dismiss）
    useScrollRegion.ts           # 滚动区 contextmenu 抑制
    events.ts / types.ts
```

### 12.2 业务接线约定

| 语义 | Panel 监听 | 说明 |
|------|-----------|------|
| 左键 | `@primary` | 替代 `@click` |
| 右键 | `@secondary` | 替代 `@contextmenu`；UiChip 默认 `suppressContextMenu` |
| 长按 / 中键 / 滚轮 | `@longPress` 等 | 按需，底层已支持 |
| 列表区外 | `useRegionOutside` | 在编排层调用，domain 不 duplicate document 监听 |

### 12.3 已删除（勿恢复）

- `useUiControlInteraction.ts`（并入 `useUiControl` + `UiControl`）
- `domains/item-list/useOutsidePointerCommit.ts`（改用 `useRegionOutside`）
- Panel 上对 Ui* 的 `@click` / `@contextmenu`
