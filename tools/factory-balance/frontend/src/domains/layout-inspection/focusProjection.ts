import type { FocusHighlight } from "../../layout/focus/focusModel";
import { isSbtoEdge } from "../../layout/focus/focusModel";
import type { LayoutEdge } from "../../api/client";
import type { LayoutFocusMode, LayoutFocusView } from "./types";

export function focusModeFromHighlight(
  highlight: FocusHighlight,
  edge?: LayoutEdge
): LayoutFocusMode {
  if (highlight.mode === "node-subtree") return "node-subtree";
  if (highlight.sbtoItem) return "sbto-chain";
  if (edge && isSbtoEdge(edge)) return "sbto-chain";
  return "belt-edge";
}

/** 钉选 highlight → 列表 / 下游只读视图 */
export function projectFocusView(
  highlight: FocusHighlight | null,
  pinned: boolean
): LayoutFocusView | null {
  if (!highlight || !pinned) return null;
  const mode: LayoutFocusMode =
    highlight.mode === "node-subtree"
      ? "node-subtree"
      : highlight.sbtoItem
        ? "sbto-chain"
        : "belt-edge";
  return {
    mode,
    itemNames: new Set(highlight.nodeIds),
    sbtoItem: highlight.sbtoItem,
    pinned: true,
  };
}
