import { Position } from "@vue-flow/core";
import type { LayoutNode } from "../api/client";
import {
  resolveSourceHandle,
  resolveTargetHandle,
  type HandleId,
} from "./nodePorts";
import type { LayoutDirection } from "./layoutTypes";

/** SBTO 边端口（LR）：同级只用左侧；跨级仍用右出/左进或回绕；受 node_kind 约束 */
export function sbtoHandleIds(
  fromGrade: number,
  toGrade: number,
  fromNode?: LayoutNode,
  toNode?: LayoutNode,
  direction: LayoutDirection = "left-to-right"
): { sourceHandle: string; targetHandle: string } {
  let source: HandleId;
  let target: HandleId;
  if (fromGrade === toGrade) {
    source = "s-l";
    target = "t-l";
  } else if (fromGrade < toGrade) {
    source = "s-r";
    target = "t-l";
  } else {
    source = "s-l";
    target = "t-r";
  }
  return {
    sourceHandle: resolveSourceHandle(fromNode, source, direction),
    targetHandle: resolveTargetHandle(toNode, target, direction),
  };
}

export function beltHandleIds(
  fromNode?: LayoutNode,
  toNode?: LayoutNode,
  direction: LayoutDirection = "left-to-right"
): { sourceHandle: string; targetHandle: string } {
  return {
    sourceHandle: resolveSourceHandle(fromNode, "s-r", direction),
    targetHandle: resolveTargetHandle(toNode, "t-l", direction),
  };
}

export function handlePosition(
  handleId: string,
  direction: "left-to-right" | "top-to-bottom"
): Position {
  const lr = direction === "left-to-right";
  switch (handleId) {
    case "s-r":
      return lr ? Position.Right : Position.Bottom;
    case "s-l":
      return lr ? Position.Left : Position.Top;
    case "t-l":
      return lr ? Position.Left : Position.Top;
    case "t-r":
      return lr ? Position.Right : Position.Bottom;
    default:
      return lr ? Position.Right : Position.Bottom;
  }
}

/** 平行边之间的法向排斥间距（像素）；SBTO+belt 同节点对沿统一法向 ±half 分开 */
export const EDGE_GAP_PX = 32;
