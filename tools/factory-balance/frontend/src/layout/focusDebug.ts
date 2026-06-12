import type { FocusHighlight } from "./focusGraph";

export const FOCUS_DEBUG_KEY = "fb-debug-focus";

export function isFocusDebugEnabled(): boolean {
  try {
    return localStorage.getItem(FOCUS_DEBUG_KEY) === "1";
  } catch {
    return false;
  }
}

export type FocusDebugEvent =
  | { kind: "node-enter"; id: string }
  | { kind: "node-leave" }
  | { kind: "edge-enter"; id: string }
  | { kind: "edge-leave" }
  | { kind: "focus"; focus: FocusHighlight | null };

export function focusDebugLog(event: FocusDebugEvent): void {
  if (!isFocusDebugEnabled()) return;
  const label =
    event.kind === "focus"
      ? event.focus
        ? `focus nodes=${event.focus.nodeIds.size} edges=${event.focus.edgeIds.size} sbto=${event.focus.sbtoItem ?? "-"}`
        : "focus cleared"
      : `${event.kind}${"id" in event ? ` ${event.id}` : ""}`;
  console.debug("[fb-focus]", label);
}

export function focusDebugSummary(focus: FocusHighlight | null): string {
  if (!focus) return "无高亮";
  const mode = focus.mode === "node-subtree" ? "节点子树" : "边";
  return `${mode} · 节点 ${focus.nodeIds.size} · 边 ${focus.edgeIds.size} · 隐藏 ${focus.hiddenEdgeIds.size}${focus.sbtoItem ? ` · SBTO ${focus.sbtoItem}` : ""}`;
}
