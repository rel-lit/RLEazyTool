import { ref } from "vue";
import { purgeCache } from "../../api/client";
import type { AppEventBus } from "../../app/events";
import type { CatalogModule } from "../catalog/useCatalog";
import { loadCatalogFromApi } from "../catalog/catalogService";
import type { useSession } from "../session/useSession";

export function usePurgeController(
  bus: AppEventBus,
  session: ReturnType<typeof useSession>,
  catalog: CatalogModule
) {
  const loading = ref(false);

  async function purge(keepActive = true): Promise<void> {
    loading.value = true;
    bus.emit({ type: "CachePurgeStarted" });

    try {
      const result = await purgeCache(keepActive);
      await session.refresh();

      const progressStillLoaded = session.progressLoaded.value;
      if (!progressStillLoaded) {
        session.clearActiveSave();
        bus.emit({ type: "ProgressCleared" });
      }

      bus.emit({
        type: "CachePurged",
        result,
        progressStillLoaded,
      });

      await loadCatalogFromApi(bus, catalog, catalog.mode.value);
    } catch (e: unknown) {
      bus.emit({
        type: "ImportFailed",
        message: e instanceof Error ? e.message : "清理缓存失败",
      });
    } finally {
      loading.value = false;
    }
  }

  return {
    loading,
    purge,
  };
}

export type PurgeModule = ReturnType<typeof usePurgeController>;
