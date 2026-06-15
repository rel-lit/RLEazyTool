import type { LayoutEdge, LayoutNode, LayoutRequest, LayoutResponse } from "../../api/client";
import { inferNodeKind } from "../../layout/nodeVisual";
import { normalizeAnalysisSummary } from "../layout-analysis/normalizeAnalysis";
import type { RecipeDetailSummary } from "../layout-analysis/types";
import { nodeByItem } from "../layout-analysis/nodeLookup";
import { resolveNodeRingRoleLabel } from "../list-layout-mark/nodeRingRole";
import { flowEdgeMediumLabel } from "./flowEdgeKind";
import type {
  InspectionBadge,
  InspectionPanelModel,
  InspectionPanelSection,
  InspectionTarget,
  LayoutFocusView,
} from "./types";

function nodeLabel(layout: LayoutResponse, id: string): string {
  const node = nodeByItem(layout.nodes, id);
  return node?.label ?? id;
}

function endpointLine(
  layout: LayoutResponse,
  itemId: string,
  request?: LayoutRequest | null
): string {
  const node = nodeByItem(layout.nodes, itemId);
  const label = node?.label ?? itemId;
  const layer = node?.layer ?? node?.meta?.layer ?? "—";
  const role = resolveNodeRingRoleLabel(itemId, layout, request);
  return `${label} · layer ${layer} · ${role}`;
}

function worldSupplyDetail(item: string, node: LayoutNode | undefined): RecipeDetailSummary | null {
  if (!node) return null;
  const label = node.label ?? item;
  const isPure = inferNodeKind(node) === "pure_source" || node.meta?.external_leaf;
  if (!isPure) return null;
  if (node.meta?.pseudo_external) {
    return {
      recipe_name: "",
      label,
      line: `假定外源 → ${label}`,
      kind: "world-supply",
    };
  }
  if (node.meta?.supply_kind === "world_baseline" || node.meta?.external_leaf) {
    return {
      recipe_name: "",
      label,
      line: `世界开采 → ${label}`,
      kind: "world-supply",
    };
  }
  return {
    recipe_name: "",
    label,
    line: `外部供给 → ${label}`,
    kind: "world-supply",
  };
}

function recipeDetailForItem(
  item: string,
  node: LayoutNode | undefined,
  details: Readonly<Record<string, RecipeDetailSummary>>,
  assignments: Readonly<Record<string, string>>
): RecipeDetailSummary | null {
  if (details[item]) return details[item];
  const rname = assignments[item] ?? node?.recipe ?? node?.meta?.recipe;
  if (!rname) return worldSupplyDetail(item, node);
  if (typeof rname === "string" && rname.startsWith("fb-extract:")) {
    const label = node?.label ?? item;
    return {
      recipe_name: rname,
      label,
      line: `世界抽取 → ${label}`,
      kind: "extract",
    };
  }
  return {
    recipe_name: String(rname),
    label: node?.label ?? item,
    line: String(rname),
    kind: "unknown",
  };
}

function buildRecipeLines(
  itemNames: Iterable<string>,
  layout: LayoutResponse,
  details: Readonly<Record<string, RecipeDetailSummary>>,
  assignments: Readonly<Record<string, string>>
): string[] {
  const sorted = [...itemNames].sort((a, b) => {
    const na = nodeByItem(layout.nodes, a);
    const nb = nodeByItem(layout.nodes, b);
    const la = na?.layer ?? 0;
    const lb = nb?.layer ?? 0;
    if (la !== lb) return lb - la;
    return (na?.label ?? a).localeCompare(nb?.label ?? b, "zh-CN");
  });

  const lines: string[] = [];
  for (const item of sorted) {
    const node = nodeByItem(layout.nodes, item);
    const label = node?.label ?? item;
    const detail = recipeDetailForItem(item, node, details, assignments);
    if (!detail) {
      lines.push(`${label}：无制造配方`);
      continue;
    }
    lines.push(`${label}：${detail.line}`);
    if (detail.kind === "unknown" && detail.line === detail.recipe_name) {
      lines.push(`  └ 内部标识 ${detail.recipe_name}（重算布局以展开完整配方）`);
    }
  }
  return lines;
}

function sbtoChainEdges(layout: LayoutResponse, sharedItem: string): LayoutEdge[] {
  return layout.edges.filter((e) => e.type === "tap_chain" && e.item === sharedItem);
}

function resolveNodePanel(
  target: InspectionTarget & { kind: "node" },
  layout: LayoutResponse,
  focusView: LayoutFocusView | null,
  request?: LayoutRequest | null
): InspectionPanelModel | null {
  const node = layout.nodes.find((n) => n.id === target.id || n.item === target.id);
  if (!node) return null;

  const analysis = normalizeAnalysisSummary(layout.analysis);
  const assignments = analysis?.recipe_assignments ?? {};
  const details = analysis?.recipe_details ?? {};
  const roleLabel = resolveNodeRingRoleLabel(node.item, layout, request);

  const sections: InspectionPanelSection[] = [
    {
      heading: "基本信息",
      lines: [`层级 layer ${node.layer}`, `类型 ${roleLabel}`],
    },
  ];

  if (focusView && focusView.itemNames.size > 0) {
    sections.push({
      heading: "相关配方",
      lines: buildRecipeLines(focusView.itemNames, layout, details, assignments),
    });
  }

  return {
    kind: "node",
    badge: "节点",
    title: node.label,
    sections,
  };
}

function resolveBeltEdgePanel(
  edge: LayoutEdge,
  layout: LayoutResponse,
  focusView: LayoutFocusView | null,
  request?: LayoutRequest | null
): InspectionPanelModel {
  const fromNode = nodeByItem(layout.nodes, edge.from);
  const toNode = nodeByItem(layout.nodes, edge.to);
  const fromLayer = fromNode?.layer ?? fromNode?.meta?.layer;
  const toLayer = toNode?.layer ?? toNode?.meta?.layer;
  const medium = flowEdgeMediumLabel(edge);
  const transportLabel = nodeLabel(layout, edge.item);

  const basicLines = [
    `上游 ${endpointLine(layout, edge.from, request)}`,
    `下游 ${endpointLine(layout, edge.to, request)}`,
    fromLayer != null && toLayer != null
      ? `层级跨度 layer ${fromLayer} → ${toLayer}`
      : "层级跨度 —",
    `输送介质 ${medium}`,
  ];
  if (transportLabel !== nodeLabel(layout, edge.from) && transportLabel !== nodeLabel(layout, edge.to)) {
    basicLines.push(`输送物 ${transportLabel}`);
  }

  const analysis = normalizeAnalysisSummary(layout.analysis);
  const assignments = analysis?.recipe_assignments ?? {};
  const details = analysis?.recipe_details ?? {};

  const sections: InspectionPanelSection[] = [{ heading: "基本信息", lines: basicLines }];

  if (focusView && focusView.itemNames.size > 0) {
    sections.push({
      heading: "相关配方",
      lines: buildRecipeLines(focusView.itemNames, layout, details, assignments),
    });
  }

  return {
    kind: "edge",
    badge: "边",
    title: `${nodeLabel(layout, edge.from)} → ${nodeLabel(layout, edge.to)}`,
    sections,
  };
}

function resolveSbtoEdgePanel(
  edge: LayoutEdge,
  layout: LayoutResponse,
  focusView: LayoutFocusView | null,
  request?: LayoutRequest | null
): InspectionPanelModel {
  const chainEdges = sbtoChainEdges(layout, edge.item);
  const totalSegments = chainEdges.length;
  const segmentIndex = edge.tap_index ?? chainEdges.findIndex((e) => e.id === edge.id) + 1;
  const sharedLabel = nodeLabel(layout, edge.item);
  const tap = layout.tap_orders.find((t) => t.item === edge.item);

  const fromNode = nodeByItem(layout.nodes, edge.from);
  const toNode = nodeByItem(layout.nodes, edge.to);
  const fromLayer = fromNode?.layer ?? "—";
  const toLayer = toNode?.layer ?? "—";

  const sections: InspectionPanelSection[] = [
    {
      heading: "基本信息",
      lines: [
        `共享物 ${sharedLabel}`,
        `本段 ${nodeLabel(layout, edge.from)}（layer ${fromLayer}）→ ${nodeLabel(layout, edge.to)}（layer ${toLayer}）`,
        totalSegments > 0
          ? `段序 第 ${segmentIndex} 段 / 共 ${totalSegments} 段`
          : "段序 —",
        `上游 ${resolveNodeRingRoleLabel(edge.from, layout, request)} · 下游 ${resolveNodeRingRoleLabel(edge.to, layout, request)}`,
      ],
    },
  ];

  const analysis = normalizeAnalysisSummary(layout.analysis);
  const assignments = analysis?.recipe_assignments ?? {};
  const details = analysis?.recipe_details ?? {};

  const chainDetailLines: string[] = [];
  if (tap) {
    chainDetailLines.push(`取用顺序 ${tap.order_labels.join(" → ")}`);
    if (tap.explanation) chainDetailLines.push(tap.explanation);
  } else if (edge.note) {
    chainDetailLines.push(edge.note);
  }

  const recipeLines =
    focusView && focusView.itemNames.size > 0
      ? buildRecipeLines(focusView.itemNames, layout, details, assignments)
      : [];

  sections.push({
    heading: "SBTO 链详情",
    lines: chainDetailLines,
    bullets: recipeLines.length > 0 ? ["涉及物品配方", ...recipeLines] : undefined,
  });

  return {
    kind: "edge",
    badge: "SBTO边",
    title: `${nodeLabel(layout, edge.from)} → ${nodeLabel(layout, edge.to)}`,
    sections,
  };
}

function resolveEdgePanel(
  target: InspectionTarget & { kind: "edge" },
  layout: LayoutResponse,
  focusView: LayoutFocusView | null,
  request?: LayoutRequest | null
): InspectionPanelModel | null {
  const edge = layout.edges.find((e) => e.id === target.id);
  if (!edge) return null;

  if (edge.type === "tap_chain") {
    return resolveSbtoEdgePanel(edge, layout, focusView, request);
  }
  return resolveBeltEdgePanel(edge, layout, focusView, request);
}

export function resolveInspectionPanel(
  target: InspectionTarget | null,
  layout: LayoutResponse | null,
  focusView: LayoutFocusView | null,
  request?: LayoutRequest | null
): InspectionPanelModel | null {
  if (!target || !layout) return null;
  if (target.kind === "node") return resolveNodePanel(target, layout, focusView, request);
  return resolveEdgePanel(target, layout, focusView, request);
}
