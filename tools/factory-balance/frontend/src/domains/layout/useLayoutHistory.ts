import { ref } from "vue";
import {
  clearLayoutHistory,
  deleteLayoutHistory,
  getLayoutHistory,
  listLayoutHistory,
  type LayoutHistoryEntry,
  type LayoutResponse,
} from "../../api/client";
import type { AppEventBus } from "../../app/events";

export function useLayoutHistory(bus: AppEventBus) {
  const entries = ref<LayoutHistoryEntry[]>([]);
  const loading = ref(false);
  const error = ref("");

  async function refresh(): Promise<void> {
    loading.value = true;
    error.value = "";
    try {
      entries.value = await listLayoutHistory(50);
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : "加载历史失败";
    } finally {
      loading.value = false;
    }
  }

  async function loadRecord(id: number): Promise<LayoutResponse | null> {
    loading.value = true;
    error.value = "";
    try {
      const detail = await getLayoutHistory(id);
      bus.emit({ type: "LayoutRestoredFromHistory", layout: detail.response });
      return detail.response;
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : "读取历史失败";
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function remove(id: number): Promise<void> {
    await deleteLayoutHistory(id);
    entries.value = entries.value.filter((e) => e.id !== id);
  }

  async function clearAll(): Promise<void> {
    await clearLayoutHistory();
    entries.value = [];
  }

  return {
    entries,
    loading,
    error,
    refresh,
    loadRecord,
    remove,
    clearAll,
  };
}

export type LayoutHistoryModule = ReturnType<typeof useLayoutHistory>;
