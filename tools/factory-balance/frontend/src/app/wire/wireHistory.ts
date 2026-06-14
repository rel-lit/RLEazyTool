import type { AppContext } from "../context";

export function wireHistory(ctx: AppContext): () => void {
  const off1 = ctx.bus.on("LayoutSnapshotSaved", () => {
    void ctx.layoutHistory.refresh();
  });
  const off2 = ctx.bus.on("CatalogLoaded", (e) => {
    if (e.mode === "progress" && e.progressStale !== undefined) {
      ctx.session.setProgressStale(Boolean(e.progressStale));
    }
  });
  return () => {
    off1();
    off2();
  };
}
