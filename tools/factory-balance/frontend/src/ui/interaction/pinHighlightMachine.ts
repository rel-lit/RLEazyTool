/** 通用 hover / pin 高亮状态机（控件、列表区、画布共用） */

export interface PinHighlightState<T> {
  dragging: boolean;
  /** 悬停预览；pointer leave 清除；已 pin 时不更新 */
  hoverHighlight: T | null;
  /** 区内 primary 锁定，直至 CLEAR 或切换 pin */
  pinnedHighlight: T | null;
}

export type PinHighlightAction<T> =
  | { type: "HOVER"; highlight: T }
  | { type: "PIN"; highlight: T }
  | { type: "POINTER_LEAVE" }
  | { type: "CLEAR" }
  | { type: "DRAG_START" }
  | { type: "DRAG_END" };

export function effectivePinHighlight<T>(state: PinHighlightState<T>): T | null {
  if (state.dragging) return null;
  return state.pinnedHighlight ?? state.hoverHighlight;
}

export function pinHighlightReducer<T>(
  state: PinHighlightState<T>,
  action: PinHighlightAction<T>
): PinHighlightState<T> {
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
    case "HOVER":
      if (state.pinnedHighlight) return state;
      return { ...state, hoverHighlight: action.highlight };
    case "PIN":
      return {
        ...state,
        pinnedHighlight: action.highlight,
        hoverHighlight: null,
      };
    default:
      return state;
  }
}

export const initialPinHighlightState = {
  dragging: false,
  hoverHighlight: null,
  pinnedHighlight: null,
} satisfies PinHighlightState<never>;
