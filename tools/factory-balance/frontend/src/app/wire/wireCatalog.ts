import type { AppContext } from "../context";

export function wireCatalog(ctx: AppContext): () => void {
  const off1 = ctx.bus.on("ProgressChanged", (e) => {
    ctx.catalog.applyProgressCatalog(e.catalog);
  });
  const off2 = ctx.bus.on("ProgressCleared", () => {
    ctx.catalog.clearCatalog();
  });
  return () => {
    off1();
    off2();
  };
}
