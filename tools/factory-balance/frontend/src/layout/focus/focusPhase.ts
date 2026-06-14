import type { FocusHighlight } from "./focusModel";

/** 画布高亮相态（由 layout 领域 highlight 推导，非 UI 状态机本身） */
export type FocusPhase =
  | "idle"
  | "node-subtree"
  | "sbto-chain"
  | "belt-edge"
  | "dragging";

export function phaseForHighlight(h: FocusHighlight | null): FocusPhase {
  if (!h) return "idle";
  if (h.mode === "node-subtree") return "node-subtree";
  if (h.mode === "edge") return h.sbtoItem ? "sbto-chain" : "belt-edge";
  return "idle";
}
