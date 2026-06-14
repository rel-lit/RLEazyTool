import type { AppActions } from "../actions/createAppActions";
import type { AppContext } from "../context";

export function wireItemList(ctx: AppContext, actions: AppActions): () => void {
  const off1 = ctx.bus.on("ProgressChanged", () => {
    actions.syncItemListsFromCatalog();
  });
  const off2 = ctx.bus.on("CatalogModeChanged", () => {
    actions.syncItemListsFromCatalog();
  });
  const off3 = ctx.bus.on("CatalogLoaded", () => {
    actions.syncItemListsFromCatalog();
  });
  return () => {
    off1();
    off2();
    off3();
  };
}
