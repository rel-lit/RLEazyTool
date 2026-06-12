import { computed, ref } from "vue";
import axios from "axios";
import {
  computeLayout,
  type LayoutEdge,
  type LayoutRequest,
  type LayoutResponse,
  type TapOrderEntry,
} from "../../api/client";
import { DEFAULT_LAYOUT_OPTIONS } from "../../app/config";
import type { AppEventBus } from "../../app/events";
import type { SelectionModule } from "../selection/useSelection";

export function useLayout(bus: AppEventBus, selection: SelectionModule, catalogMode: { value: "progress" | "full" }) {
  const layout = ref<LayoutResponse | null>(null);
  const selectedEdgeId = ref<string | null>(null);
  const loading = ref(false);
  const error = ref("");
  const stale = ref(false);

  const selectedEdge = computed<LayoutEdge | null>(
    () => layout.value?.edges.find((e) => e.id === selectedEdgeId.value) ?? null
  );

  const selectedTap = computed<TapOrderEntry | null>(() => {
    if (!selectedEdge.value) return null;
    return layout.value?.tap_orders.find((t) => t.item === selectedEdge.value?.item) ?? null;
  });

  const analysisWarnings = computed(() => layout.value?.warnings ?? []);

  function reset(): void {
    layout.value = null;
    selectedEdgeId.value = null;
    error.value = "";
    stale.value = false;
  }

  function invalidate(reason: string): void {
    if (layout.value) stale.value = true;
    selectedEdgeId.value = null;
    error.value = "";
    bus.emit({ type: "LayoutInvalidated", reason });
  }

  function selectEdge(id: string | null): void {
    selectedEdgeId.value = id;
  }

  async function compute(): Promise<void> {
    if (!selection.selectedTargets.value.length) {
      error.value = "请至少选择一个产出物";
      return;
    }
    loading.value = true;
    error.value = "";
    selectedEdgeId.value = null;
    stale.value = false;
    bus.emit({ type: "LayoutComputeStarted" });

    const body: LayoutRequest = {
      targets: selection.selectedTargets.value.map((item) => ({ item })),
      supply_mode: selection.supplyMode.value,
      supplied_items: [...selection.suppliedItems.value],
      forbidden_items: [...selection.forbiddenItems.value],
      catalog_mode: catalogMode.value,
      layout_options: { ...DEFAULT_LAYOUT_OPTIONS },
    };

    try {
      layout.value = await computeLayout(body);
      if (layout.value.analysis?.impossible) {
        error.value = "当前约束下无法实现所选产出";
      }
      bus.emit({ type: "LayoutComputed", layout: layout.value });
    } catch (e: unknown) {
      let message = e instanceof Error ? e.message : "计算失败";
      if (axios.isAxiosError(e) && e.code === "ECONNABORTED") {
        message = "计算超时，目标生产链可能过大或存在循环依赖";
      }
      error.value = message;
      layout.value = null;
      bus.emit({ type: "LayoutComputeFailed", message });
    } finally {
      loading.value = false;
    }
  }

  bus.on("ProgressChanged", () => reset());
  bus.on("ProgressCleared", () => reset());
  bus.on("SelectionChanged", () => invalidate("selection-changed"));

  return {
    layout,
    selectedEdgeId,
    loading,
    error,
    stale,
    selectedEdge,
    selectedTap,
    analysisWarnings,
    reset,
    invalidate,
    selectEdge,
    compute,
  };
}

export type LayoutModule = ReturnType<typeof useLayout>;
