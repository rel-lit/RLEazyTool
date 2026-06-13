import type { FocusHighlight } from "./focusModel";

/** 画布 focus 相态（由 effective highlight 推导，dragging 除外） */
export type FocusPhase =
  | "idle"
  | "node-subtree"
  | "sbto-chain"
  | "belt-edge"
  | "dragging";

export interface FocusMachineState {
  dragging: boolean;
  /** 悬停预览（pointer leave 清除；pinned 时不更新） */
  hoverHighlight: FocusHighlight | null;
  /** 画布内点击锁定，直至 pane/其它元素点击 */
  pinnedHighlight: FocusHighlight | null;
}

export type FocusAction =
  | { type: "HOVER_NODE"; highlight: FocusHighlight }
  | { type: "HOVER_EDGE"; highlight: FocusHighlight }
  | { type: "PIN_NODE"; highlight: FocusHighlight }
  | { type: "PIN_EDGE"; highlight: FocusHighlight }
  | { type: "POINTER_LEAVE" }
  | { type: "CLEAR" }
  | { type: "DRAG_START" }
  | { type: "DRAG_END" };

export function phaseForHighlight(h: FocusHighlight | null): FocusPhase {
  if (!h) return "idle";
  if (h.mode === "node-subtree") return "node-subtree";
  if (h.mode === "edge") return h.sbtoItem ? "sbto-chain" : "belt-edge";
  return "idle";
}

export function effectiveHighlight(state: FocusMachineState): FocusHighlight | null {
  if (state.dragging) return null;
  return state.pinnedHighlight ?? state.hoverHighlight;
}

export function focusReducer(
  state: FocusMachineState,
  action: FocusAction
): FocusMachineState {
  switch (action.type) {
    case "DRAG_START":
      return { ...state, dragging: true, hoverHighlight: null };
    case "DRAG_END":
      return { ...state, dragging: false, hoverHighlight: null };
    case "CLEAR":
      return { dragging: false, hoverHighlight: null, pinnedHighlight: null };
    case "POINTER_LEAVE":
      if (state.pinnedHighlight) return { ...state, hoverHighlight: null };
      return { ...state, hoverHighlight: null };
    case "HOVER_NODE":
    case "HOVER_EDGE":
      if (state.pinnedHighlight) return state;
      return { ...state, hoverHighlight: action.highlight };
    case "PIN_NODE":
    case "PIN_EDGE":
      return {
        ...state,
        pinnedHighlight: action.highlight,
        hoverHighlight: null,
      };
    default:
      return state;
  }
}

export const initialFocusState: FocusMachineState = {
  dragging: false,
  hoverHighlight: null,
  pinnedHighlight: null,
};
