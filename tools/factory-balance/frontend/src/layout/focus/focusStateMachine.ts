import type { FocusHighlight } from "./focusModel";

/** 画布 focus 相态：交互驱动，单一来源 */
export type FocusPhase =
  | "idle"
  | "node-subtree"
  | "sbto-chain"
  | "belt-edge"
  | "dragging";

export interface FocusMachineState {
  phase: FocusPhase;
  highlight: FocusHighlight | null;
}

export type FocusAction =
  | { type: "HOVER_NODE"; highlight: FocusHighlight }
  | { type: "HOVER_EDGE"; highlight: FocusHighlight }
  | { type: "POINTER_LEAVE" }
  | { type: "CLEAR" }
  | { type: "DRAG_START" }
  | { type: "DRAG_END" };

function phaseForEdgeHighlight(h: FocusHighlight): FocusPhase {
  if (h.mode !== "edge") return "idle";
  return h.sbtoItem ? "sbto-chain" : "belt-edge";
}

export function focusReducer(
  state: FocusMachineState,
  action: FocusAction
): FocusMachineState {
  switch (action.type) {
    case "DRAG_START":
      return { phase: "dragging", highlight: null };
    case "DRAG_END":
      return { phase: "idle", highlight: null };
    case "CLEAR":
    case "POINTER_LEAVE":
      return { phase: "idle", highlight: null };
    case "HOVER_NODE":
      return { phase: "node-subtree", highlight: action.highlight };
    case "HOVER_EDGE":
      return {
        phase: phaseForEdgeHighlight(action.highlight),
        highlight: action.highlight,
      };
    default:
      return state;
  }
}

export const initialFocusState: FocusMachineState = {
  phase: "idle",
  highlight: null,
};
