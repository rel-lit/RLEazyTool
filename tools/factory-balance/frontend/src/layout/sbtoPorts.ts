import { Position } from "@vue-flow/core";

/** SBTO 边端口（LR）：同级只用左侧；跨级仍用右出/左进或回绕 */
export function sbtoHandleIds(
  fromGrade: number,
  toGrade: number
): { sourceHandle: string; targetHandle: string } {
  if (fromGrade === toGrade) {
    return { sourceHandle: "s-l", targetHandle: "t-l" };
  }
  if (fromGrade < toGrade) {
    return { sourceHandle: "s-r", targetHandle: "t-l" };
  }
  return { sourceHandle: "s-l", targetHandle: "t-r" };
}

export function beltHandleIds(): {
  sourceHandle: string;
  targetHandle: string;
} {
  return { sourceHandle: "s-r", targetHandle: "t-l" };
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

/** 平行边之间的法向排斥间距（像素） */
export const EDGE_GAP_PX = 28;
