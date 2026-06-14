import type { AppContext } from "../context";
import { loadCatalogFromApi } from "../../domains/catalog/catalogService";

export function wireProgress(ctx: AppContext): () => void {
  const off1 = ctx.bus.on("ProgressChanged", async (e) => {
    ctx.session.setActiveSaveKey(e.saveKey, Boolean(e.progressStale));
    await ctx.session.refresh();
  });
  const off2 = ctx.bus.on("BootstrapComplete", () => {
    if (!ctx.session.progressLoaded.value) {
      ctx.bus.emit({ type: "ProgressCleared" });
    }
  });
  return () => {
    off1();
    off2();
  };
}

export async function bootstrapApp(ctx: AppContext): Promise<void> {
  ctx.bus.emit({ type: "BootstrapStarted" });
  await ctx.session.refresh();
  await loadCatalogFromApi(ctx.bus, ctx.catalog, "progress");
  ctx.bus.emit({ type: "BootstrapComplete" });
}
