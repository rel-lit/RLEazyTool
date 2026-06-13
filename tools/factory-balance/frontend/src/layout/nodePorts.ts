import type { LayoutNode } from "../api/client";
import { inferNodeKind } from "./nodeVisual";
import type { LayoutDirection } from "./layoutTypes";

export type HandleId = "t-l" | "t-r" | "s-l" | "s-r";

const ALL_HANDLES: HandleId[] = ["t-l", "t-r", "s-l", "s-r"];

/** 纯粹原料：禁止左侧端口；终端产物：禁止右侧端口（LR/TB 与 sbtoPorts 一致） */
export function isHandleAllowedForNode(
  node: LayoutNode | undefined,
  handleId: HandleId,
  _direction: LayoutDirection = "left-to-right"
): boolean {
  if (!node) return true;
  const kind = inferNodeKind(node);
  const isLeft = handleId === "t-l" || handleId === "s-l";
  const isRight = handleId === "t-r" || handleId === "s-r";
  if (kind === "pure_source" && isLeft) return false;
  if (kind === "terminal" && isRight) return false;
  return true;
}

export function nodeHandleVisibility(
  node: LayoutNode,
  direction: LayoutDirection = "left-to-right"
): Record<HandleId, boolean> {
  return Object.fromEntries(
    ALL_HANDLES.map((id) => [id, isHandleAllowedForNode(node, id, direction)])
  ) as Record<HandleId, boolean>;
}

const SOURCE_PREFERENCE: HandleId[] = ["s-r", "s-l"];
const TARGET_PREFERENCE: HandleId[] = ["t-l", "t-r"];

export function resolveSourceHandle(
  node: LayoutNode | undefined,
  preferred: HandleId,
  direction: LayoutDirection = "left-to-right"
): HandleId {
  if (isHandleAllowedForNode(node, preferred, direction)) return preferred;
  for (const id of SOURCE_PREFERENCE) {
    if (isHandleAllowedForNode(node, id, direction)) return id;
  }
  return preferred;
}

export function resolveTargetHandle(
  node: LayoutNode | undefined,
  preferred: HandleId,
  direction: LayoutDirection = "left-to-right"
): HandleId {
  if (isHandleAllowedForNode(node, preferred, direction)) return preferred;
  for (const id of TARGET_PREFERENCE) {
    if (isHandleAllowedForNode(node, id, direction)) return id;
  }
  return preferred;
}
