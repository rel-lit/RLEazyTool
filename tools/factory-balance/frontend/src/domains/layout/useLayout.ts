import { computed, ref, type Ref } from "vue";
import axios from "axios";
import {
  computeLayout,
  type LayoutRequest,
  type LayoutResponse,
} from "../../api/client";
import type { AppEventBus } from "../../app/events";
import type { LayoutPersistence } from "./layoutPersistence";
import type { SelectionModule } from "../selection/useSelection";
import { buildLayoutRequest } from "./layoutSnapshot";

export type NodePositionMap = Record<string, { x: number; y: number }>;

export function useLayout(
  bus: AppEventBus,
  selection: SelectionModule,
  catalogMode: { value: "progress" | "full" },
  persistence: LayoutPersistence,
  boundRequestRef: Ref<LayoutRequest | null>
) {
  const layout = ref<LayoutResponse | null>(null);
  const loading = ref(false);
  const error = ref("");
  const stale = ref(false);

  const boundRequest = boundRequestRef;

  const analysisWarnings = computed(() => layout.value?.warnings ?? []);

  function reset(): void {
    layout.value = null;
    error.value = "";
    stale.value = false;
    boundRequestRef.value = null;
  }

  function invalidate(reason: string): void {
    if (layout.value) stale.value = true;
    error.value = "";
    bus.emit({ type: "LayoutInvalidated", reason });
  }

  async function compute(): Promise<void> {
    if (!selection.selectedTargets.value.length) {
      error.value = "请至少选择一个产出物";
      return;
    }
    loading.value = true;
    error.value = "";
    stale.value = false;

    await persistence.saveBeforeRecompute();

    bus.emit({ type: "LayoutComputeStarted", resetPositions: true });

    const body: LayoutRequest = buildLayoutRequest(selection, catalogMode.value);

    try {
      layout.value = await computeLayout(body);
      if (layout.value.analysis?.impossible) {
        error.value = "当前约束下无法实现所选产出";
        boundRequestRef.value = null;
      } else {
        boundRequestRef.value = body;
      }
      bus.emit({ type: "LayoutComputed", layout: layout.value });
    } catch (e: unknown) {
      let message = e instanceof Error ? e.message : "计算失败";
      if (axios.isAxiosError(e) && e.code === "ECONNABORTED") {
        message = "计算超时，目标生产链可能过大或存在循环依赖";
      }
      error.value = message;
      layout.value = null;
      boundRequestRef.value = null;
      bus.emit({ type: "LayoutComputeFailed", message });
    } finally {
      loading.value = false;
    }
  }

  function applyLayout(data: LayoutResponse, request?: LayoutRequest): void {
    layout.value = data;
    error.value = "";
    stale.value = false;
    if (request) {
      boundRequestRef.value = request;
    }
    if (data.analysis?.impossible) {
      error.value = "当前约束下无法实现所选产出";
    }
  }

  return {
    layout,
    boundRequest,
    loading,
    error,
    stale,
    analysisWarnings,
    reset,
    invalidate,
    compute,
    applyLayout,
  };
}

export type LayoutModule = ReturnType<typeof useLayout>;
