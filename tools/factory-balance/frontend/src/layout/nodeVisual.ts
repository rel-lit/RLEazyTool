import type { LayoutNode } from "../api/client";

export type NodeKind = "pure_source" | "terminal" | "intermediate";

export interface NodeVisual {
  background: string;
  borderColor: string;
  borderStyle: "solid" | "dashed";
  borderWidth: string;
}

/** 常态节点不透明度（90% 不透明） */
export const NODE_BASE_OPACITY = 0.9;

const PURE_SOURCE = { h: 137, s: 61, l: 35 };
const TERMINAL = { h: 263, s: 52, l: 58 };
/** 中间物：马卡龙哑光感（降饱和、略暗于终端），仅色相随 layer 蓝→青 */
const INTERMEDIATE_S = 42;
const INTERMEDIATE_L = 50;
const INTERMEDIATE_HUE_LOW = 232;
const INTERMEDIATE_HUE_HIGH = 162;

function hsla(h: number, s: number, l: number, a: number): string {
  return `hsla(${h}, ${s}%, ${l}%, ${a})`;
}

function isExtractRecipe(node: LayoutNode): boolean {
  return node.recipe_type === "extraction";
}

export function inferNodeKind(node: LayoutNode): NodeKind {
  const kind = node.meta?.node_kind;
  if (kind === "pure_source" || kind === "terminal" || kind === "intermediate") {
    return kind;
  }
  if (node.meta?.external_leaf && !node.meta?.pseudo_external) {
    return "pure_source";
  }
  if (node.meta?.role === "terminal") {
    return "terminal";
  }
  return "intermediate";
}

export function layoutMaxLayer(nodes: LayoutNode[], analysisMax?: number): number {
  if (typeof analysisMax === "number" && analysisMax >= 0) {
    return analysisMax;
  }
  if (nodes.length === 0) return 0;
  return Math.max(...nodes.map((n) => n.layer ?? n.meta?.layer ?? 0));
}

/** 由后端 meta + layer 解析节点呈现色（不含 focus dim；背景为实色，透明度由 .fb-node opacity 控制） */
export function resolveNodeVisual(
  node: LayoutNode,
  maxLayer: number
): NodeVisual {
  const kind = inferNodeKind(node);
  const extract = isExtractRecipe(node);
  const pseudo = !!node.meta?.pseudo_external;
  const worldBaseline = node.meta?.supply_kind === "world_baseline";

  if (kind === "pure_source") {
    const base = worldBaseline
      ? { h: 140, s: 48, l: 22 }
      : PURE_SOURCE;
    return {
      background: hsla(base.h, base.s, base.l, 1),
      borderColor: worldBaseline ? "#3fb950" : "#484f58",
      borderStyle: pseudo ? "dashed" : "solid",
      borderWidth: worldBaseline ? "2px" : "1px",
    };
  }

  if (kind === "terminal") {
    return {
      background: hsla(TERMINAL.h, TERMINAL.s, TERMINAL.l, 1),
      borderColor: "#484f58",
      borderStyle: "solid",
      borderWidth: "1px",
    };
  }

  const layer = node.layer ?? node.meta?.layer ?? 0;
  const t = maxLayer > 0 ? layer / maxLayer : 0;
  const hue =
    INTERMEDIATE_HUE_LOW + t * (INTERMEDIATE_HUE_HIGH - INTERMEDIATE_HUE_LOW);

  return {
    background: hsla(hue, INTERMEDIATE_S, INTERMEDIATE_L, 1),
    borderColor: extract ? "#6e9eb8" : "#484f58",
    borderStyle: extract ? "dashed" : "solid",
    borderWidth: "1px",
  };
}

export function nodeVisualStyle(
  node: LayoutNode,
  maxLayer: number
): Record<string, string> {
  const v = resolveNodeVisual(node, maxLayer);
  return {
    "--fb-bg": v.background,
    "--fb-border": v.borderColor,
    "--fb-border-style": v.borderStyle,
    "--fb-border-width": v.borderWidth,
  };
}
