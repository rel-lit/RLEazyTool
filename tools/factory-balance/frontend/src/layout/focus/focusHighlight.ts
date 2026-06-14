import type { FocusHighlight } from "./focusModel";
import { isHiddenEdge, isSbtoEdge } from "./focusModel";
import type { LayoutEdge } from "../../api/client";
import type { FocusPhase } from "./focusPhase";

export function isNodeHighlighted(
  nodeId: string,
  focus: FocusHighlight | null
): boolean {
  if (!focus) return true;
  return focus.nodeIds.has(nodeId);
}

export function isEdgeHighlighted(
  edge: LayoutEdge,
  focus: FocusHighlight | null
): boolean {
  if (!focus) return true;
  if (isHiddenEdge(edge)) {
    return focus.hiddenEdgeIds.has(edge.id);
  }
  if (isSbtoEdge(edge)) {
    if (focus.mode === "node-subtree") {
      return false;
    }
    return focus.edgeIds.has(edge.id);
  }
  return focus.edgeIds.has(edge.id);
}

/** SBTO 虚线流动：仅在 sbto-chain 相态 */
export function sbtoFlowActive(
  edge: LayoutEdge,
  phase: FocusPhase,
  focus: FocusHighlight | null
): boolean {
  if (phase !== "sbto-chain" || !focus?.sbtoItem) return false;
  return isSbtoEdge(edge) && edge.item === focus.sbtoItem;
}
