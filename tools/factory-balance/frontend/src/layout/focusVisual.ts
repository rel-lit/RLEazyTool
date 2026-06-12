/**
 * 悬停高亮绘制：直接操作 Vue Flow 已渲染的 DOM，不修改 nodes/edges 状态。
 */
import type { FocusHighlight } from "./focusGraph";

export function paintFocusVisual(
  container: HTMLElement | null,
  focus: FocusHighlight | null
): void {
  if (!container) return;

  container.querySelectorAll(".vue-flow__node").forEach((el) => {
    if (!(el instanceof HTMLElement)) return;
    const id = el.getAttribute("data-id") ?? "";
    const lit = !focus || focus.nodeIds.has(id);
    el.classList.toggle("vf-dim", !lit);
    el.classList.toggle("vf-lit", lit);
  });

  container.querySelectorAll(".vue-flow__edge").forEach((el) => {
    if (!(el instanceof HTMLElement)) return;
    const id = el.getAttribute("data-id") ?? "";
    const isHiddenOverlay = id.startsWith("hidden-");

    if (isHiddenOverlay) {
      const show =
        focus?.mode === "node-subtree" && focus.hiddenEdgeIds.has(id);
      if (!show) {
        el.style.display = "none";
        el.classList.remove("vf-dim", "vf-lit");
      } else {
        el.style.display = "";
      }
      return;
    }

    const isSbto =
      el.classList.contains("vue-flow__edge-sbto") ||
      el.querySelector(".sbto-edge") != null;

    let lit = !focus;
    if (focus) {
      if (isSbto && focus.mode === "node-subtree") {
        lit = false;
      } else {
        lit = focus.edgeIds.has(id);
      }
    }

    el.classList.toggle("vf-dim", !lit);
    el.querySelectorAll(".vue-flow__edge-path").forEach((path) => {
      if (path instanceof SVGElement) {
        path.style.opacity = lit ? "1" : "0.12";
      }
    });
  });
}

export function clearFocusVisual(container: HTMLElement | null): void {
  paintFocusVisual(container, null);
}
