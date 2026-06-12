import { fetchItemCatalog } from "../../api/client";
import type { AppEventBus } from "../../app/events";
import type { CatalogModule } from "./useCatalog";

export async function loadCatalogFromApi(
  bus: AppEventBus,
  catalog: CatalogModule,
  mode: "progress" | "full"
): Promise<void> {
  catalog.loading.value = true;
  try {
    const res = await fetchItemCatalog(mode);
    catalog.setMode(mode);
    catalog.applyPayload({
      manufacture_items: res.manufacture_items,
      supply_items: res.supply_items,
    });
    bus.emit({
      type: "CatalogModeChanged",
      mode,
    });
    bus.emit({
      type: "CatalogLoaded",
      mode,
      catalog: {
        manufacture_items: res.manufacture_items,
        supply_items: res.supply_items,
      },
      progressLoaded: res.progress_loaded,
      progressStale: res.progress_stale,
      activeSaveKey: res.active_save_key,
      hasRecipePack: res.has_recipe_pack,
    });
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : "加载物品列表失败";
    bus.emit({ type: "CatalogLoadFailed", message });
  } finally {
    catalog.loading.value = false;
  }
}
