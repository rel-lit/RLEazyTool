/**
 * nodeRingRole 与 resolveInspectionPanel 单元测试
 * 运行：npx tsx tests/layout-inspection.test.ts（需在 frontend 目录）
 */
import assert from "node:assert/strict";
import type { LayoutResponse } from "../src/api/client";
import type { FocusHighlight } from "../src/layout/focus/focusModel";
import {
  projectFocusView,
  focusModeFromHighlight,
  resolveInspectionPanel,
} from "../src/domains/layout-inspection";
import { hasListFocusRing } from "../src/domains/item-list";
import { resolveNodeRingRoleLabel } from "../src/domains/list-layout-mark";
import { flowEdgeMediumLabel } from "../src/domains/layout-inspection/flowEdgeKind";

function highlight(
  nodeIds: string[],
  mode: FocusHighlight["mode"] = "node-subtree"
): FocusHighlight {
  return {
    nodeIds: new Set(nodeIds),
    edgeIds: new Set(),
    hiddenEdgeIds: new Set(),
    dimSbtoItems: new Set(),
    sbtoItem: null,
    mode,
  };
}

assert.equal(projectFocusView(null, true), null);

const pinned = projectFocusView(highlight(["iron-plate", "iron-gear-wheel"]), true)!;
assert.equal(pinned.mode, "node-subtree");

const beltFocus = projectFocusView(highlight(["iron-plate", "iron-gear-wheel"], "edge"), true)!;

const layout: LayoutResponse = {
  nodes: [
    {
      id: "iron-plate",
      type: "item",
      item: "iron-plate",
      label: "铁板",
      layer: 2,
      position: { x: 0, y: 0 },
      meta: { node_kind: "intermediate" },
    },
    {
      id: "iron-gear-wheel",
      type: "item",
      item: "iron-gear-wheel",
      label: "铁齿轮",
      layer: 1,
      position: { x: 0, y: 0 },
      meta: { node_kind: "terminal", role: "terminal" },
    },
    {
      id: "passive-provider-chest",
      type: "item",
      item: "passive-provider-chest",
      label: "被动供货箱（红箱）",
      layer: 5,
      position: { x: 0, y: 0 },
      meta: { node_kind: "terminal", role: "terminal" },
    },
  ],
  edges: [
    {
      id: "belt-1",
      type: "belt",
      item: "iron-plate",
      label: "铁板",
      from: "iron-plate",
      to: "iron-gear-wheel",
    },
  ],
  product_edges: [],
  hidden_edges: [],
  tap_orders: [],
  warnings: [],
  layout_direction: "left-to-right",
  analysis: {
    effective_terminals: ["iron-gear-wheel", "passive-provider-chest"],
    declared_outputs: ["passive-provider-chest"],
    demoted_outputs: [],
    analysis_items: ["iron-plate", "iron-gear-wheel", "passive-provider-chest"],
    pseudo_pure_sources: [],
    recipe_assignments: {
      "iron-plate": "assigned-recipe",
      "iron-gear-wheel": "igw-recipe",
    },
    recipe_details: {
      "iron-plate": {
        recipe_name: "assigned-recipe",
        label: "铁板",
        line: "铁矿石×1 → 铁板×1",
        kind: "craft",
      },
      "iron-gear-wheel": {
        recipe_name: "igw-recipe",
        label: "铁齿轮",
        line: "铁板×2 → 铁齿轮×1",
        kind: "craft",
      },
    },
    impossible: false,
  },
};

assert.equal(resolveNodeRingRoleLabel("passive-provider-chest", layout), "有效终端");
assert.equal(flowEdgeMediumLabel(layout.edges[0]), "传送带");

const nodePanel = resolveInspectionPanel(
  { kind: "node", id: "passive-provider-chest" },
  layout,
  projectFocusView(highlight(["passive-provider-chest"]), true)
);
assert.ok(nodePanel);
assert.equal(nodePanel!.badge, "节点");
assert.equal(nodePanel!.title, "被动供货箱（红箱）");
assert.ok(!("subtitle" in nodePanel! && nodePanel!.subtitle?.includes("passive-provider")));
assert.equal(nodePanel!.sections[0].lines[1], "类型 有效终端");
assert.ok(nodePanel!.sections.some((s) => s.heading === "相关配方"));

const edgePanel = resolveInspectionPanel(
  { kind: "edge", id: "belt-1" },
  layout,
  beltFocus
);
assert.ok(edgePanel);
assert.equal(edgePanel!.badge, "边");
assert.equal(edgePanel!.title, "铁板 → 铁齿轮");
assert.equal(edgePanel!.sections[0].heading, "基本信息");
assert.ok(edgePanel!.sections[0].lines.some((l) => l.startsWith("上游")));
assert.ok(edgePanel!.sections[0].lines.some((l) => l.includes("输送介质 传送带")));
assert.ok(edgePanel!.sections.some((s) => s.heading === "相关配方"));
assert.equal(edgePanel!.sections.some((s) => s.heading === "连接"), false);

console.log("layout-inspection.test.ts OK");
