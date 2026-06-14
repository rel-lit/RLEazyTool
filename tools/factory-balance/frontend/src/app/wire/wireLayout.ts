import type { AppActions } from "../actions/createAppActions";
import type { AppContext } from "../context";

export function wireLayout(ctx: AppContext, actions: AppActions): () => void {
  const off1 = ctx.bus.on("ProgressChanged", () => {
    ctx.layout.reset();
    ctx.listLayoutMark.clearLayoutSnapshot();
  });
  const off2 = ctx.bus.on("ProgressCleared", () => {
    ctx.layout.reset();
    ctx.listLayoutMark.clearLayoutSnapshot();
  });
  const off3 = ctx.bus.on("SelectionChanged", () => {
    ctx.layout.invalidate("selection-changed");
  });
  const off4 = ctx.bus.on("LayoutComputed", (e) => {
    if (e.layout.analysis?.impossible) return;
    const request = ctx.layout.boundRequest.value;
    if (request) actions.refreshItemLists(e.layout, request);
  });
  const off5 = ctx.bus.on("LayoutRestoredFromHistory", (e) => {
    ctx.layout.applyLayout(e.layout, e.request);
    ctx.canvasLayoutHooks.prepareForNewLayout();
    actions.refreshItemLists(e.layout, e.request);
  });
  const off6 = ctx.bus.on("LayoutComputeStarted", (e) => {
    if (e.resetPositions) ctx.canvasLayoutHooks.prepareForNewLayout();
  });
  return () => {
    off1();
    off2();
    off3();
    off4();
    off5();
    off6();
  };
}
