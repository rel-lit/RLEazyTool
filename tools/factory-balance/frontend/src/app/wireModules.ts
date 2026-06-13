import type { AppEventBus } from "./events";
import { loadCatalogFromApi } from "../domains/catalog/catalogService";
import type { CatalogModule } from "../domains/catalog/useCatalog";
import type { LayoutModule } from "../domains/layout/useLayout";
import type { LayoutHistoryModule } from "../domains/layout/useLayoutHistory";
import type { SelectionModule } from "../domains/selection/useSelection";
import type { useSession } from "../domains/session/useSession";

export interface AppModules {
  bus: AppEventBus;
  session: ReturnType<typeof useSession>;
  catalog: CatalogModule;
  selection: SelectionModule;
  layout: LayoutModule;
  layoutHistory: LayoutHistoryModule;
}

/** 跨模块联动规则：单一入口，避免 App.vue 里散落 await 链 */
export function wireAppModules(modules: AppModules): void {
  const { bus, session, catalog, selection, layoutHistory } = modules;

  bus.on("ProgressChanged", async (e) => {
    session.setActiveSaveKey(e.saveKey, Boolean(e.progressStale));
    await session.refresh();
  });

  bus.on("CatalogModeChanged", () => {
    selection.pruneGhost(catalog.manufactureItems.value, catalog.supplyItems.value);
  });

  bus.on("CatalogLoaded", (e) => {
    if (e.mode === "progress" && e.progressStale !== undefined) {
      session.setProgressStale(Boolean(e.progressStale));
    }
  });

  bus.on("BootstrapComplete", () => {
    if (!session.progressLoaded.value) {
      bus.emit({ type: "ProgressCleared" });
    }
  });

  bus.on("LayoutComputed", () => {
    void layoutHistory.refresh();
  });
}

export async function bootstrapApp(modules: AppModules): Promise<void> {
  const { bus, session, catalog } = modules;
  bus.emit({ type: "BootstrapStarted" });
  await session.refresh();
  await loadCatalogFromApi(bus, catalog, "progress");
  bus.emit({ type: "BootstrapComplete" });
}

export { loadCatalogFromApi };
