import { ref } from "vue";
import { getFactorioStatus, listSaves, type FactorioStatus, type SaveInfo } from "../../api/client";
import type { AppEventBus } from "../../app/events";

export function useSession(bus: AppEventBus) {
  const status = ref<FactorioStatus | null>(null);
  const saves = ref<SaveInfo[]>([]);
  const activeSaveKey = ref<string | null>(null);
  const loading = ref(false);

  const progressLoaded = ref(false);
  const progressStale = ref(false);

  async function refresh(): Promise<void> {
    loading.value = true;
    try {
      status.value = await getFactorioStatus();
      saves.value = await listSaves();
      progressLoaded.value = status.value.progress_loaded;
      progressStale.value = Boolean(status.value.progress_stale);
      if (status.value.active_save_key) {
        activeSaveKey.value = status.value.active_save_key;
      } else if (status.value.progress_loaded && status.value.last_played_save) {
        activeSaveKey.value = activeSaveKey.value ?? status.value.last_played_save;
      }
      bus.emit({ type: "SessionRefreshed", status: status.value });
    } catch {
      // SessionRefreshed 不 emit，由调用方处理错误文案
    } finally {
      loading.value = false;
    }
  }

  function setActiveSaveKey(saveKey: string, stale = false): void {
    activeSaveKey.value = saveKey;
    progressLoaded.value = true;
    progressStale.value = stale;
  }

  function setProgressStale(stale: boolean): void {
    progressStale.value = stale;
  }

  function clearActiveSave(): void {
    activeSaveKey.value = null;
    progressLoaded.value = false;
    progressStale.value = false;
  }

  return {
    status,
    saves,
    activeSaveKey,
    progressLoaded,
    progressStale,
    loading,
    refresh,
    setActiveSaveKey,
    setProgressStale,
    clearActiveSave,
  };
}
