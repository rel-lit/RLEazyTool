import type { AppContext } from "../context";

export function wireSelection(ctx: AppContext): () => void {
  const off1 = ctx.bus.on("ProgressChanged", (e) => {
    ctx.selection.bindSaveAndReset(e.saveKey);
  });
  const off2 = ctx.bus.on("ProgressCleared", () => {
    ctx.selection.clearSaveBindingAndReset();
  });
  const off3 = ctx.bus.on("CatalogModeChanged", () => {
    ctx.selection.pruneGhost(
      ctx.catalog.manufactureItems.value,
      ctx.catalog.supplyItems.value
    );
  });
  return () => {
    off1();
    off2();
    off3();
  };
}
