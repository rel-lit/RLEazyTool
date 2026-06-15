import { computed, ref, type Ref } from "vue";
import axios from "axios";
import {
  computeLayout,
  previewLayoutRecipes,
  type LayoutRequest,
  type LayoutResponse,
  type RecipeAssignmentPreview,
} from "../../api/client";
import type { AppEventBus } from "../../app/events";
import type { LayoutPersistence } from "./layoutPersistence";
import type { SelectionModule } from "../selection/useSelection";
import { buildLayoutRequest } from "./layoutSnapshot";

export type NodePositionMap = Record<string, { x: number; y: number }>;

export interface PendingRecipePreview {
  request: LayoutRequest;
  items: RecipeAssignmentPreview[];
  confirmedAssignments: Record<string, string>;
}

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
  const pendingRecipePreview = ref<PendingRecipePreview | null>(null);

  const boundRequest = boundRequestRef;

  const analysisWarnings = computed(() => layout.value?.warnings ?? []);

  function reset(): void {
    layout.value = null;
    error.value = "";
    stale.value = false;
    boundRequestRef.value = null;
    pendingRecipePreview.value = null;
  }

  function invalidate(reason: string): void {
    if (layout.value) stale.value = true;
    error.value = "";
    bus.emit({ type: "LayoutInvalidated", reason });
  }

  async function compute(recipeAssignments?: Record<string, string>): Promise<void> {
    if (!selection.selectedTargets.value.length) {
      error.value = "请至少选择一个产出物";
      return;
    }
    loading.value = true;
    error.value = "";
    stale.value = false;
    pendingRecipePreview.value = null;

    await persistence.saveBeforeRecompute();

    bus.emit({ type: "LayoutComputeStarted", resetPositions: true });

    const body: LayoutRequest = buildLayoutRequest(selection, catalogMode.value);
    const assignments = recipeAssignments || {};
    if (Object.keys(assignments).length > 0) {
      body.recipe_assignments = assignments;
    }

    await resolveAndCompute(body, assignments);
  }

  async function resolveAndCompute(
    body: LayoutRequest,
    confirmedAssignments: Record<string, string>
  ): Promise<void> {
    try {
      const preview = await previewLayoutRecipes(body);
      if (preview.ambiguous_items.length > 0) {
        pendingRecipePreview.value = {
          request: body,
          items: preview.ambiguous_items,
          confirmedAssignments,
        };
        loading.value = false;
        return;
      }

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

  function confirmRecipeAssignments(assignments: Record<string, string>): void {
    const preview = pendingRecipePreview.value;
    if (!preview) return;
    const merged = { ...preview.confirmedAssignments, ...assignments };
    const body = { ...preview.request };
    body.recipe_assignments = merged;
    pendingRecipePreview.value = null;
    loading.value = true;
    void resolveAndCompute(body, merged);
  }

  function cancelRecipePreview(): void {
    pendingRecipePreview.value = null;
    loading.value = false;
    stale.value = false;
    bus.emit({ type: "LayoutComputeCancelled" });
  }

  function applyLayout(data: LayoutResponse, request?: LayoutRequest): void {
    layout.value = data;
    error.value = "";
    stale.value = false;
    pendingRecipePreview.value = null;
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
    pendingRecipePreview,
    reset,
    invalidate,
    compute,
    confirmRecipeAssignments,
    cancelRecipePreview,
    applyLayout,
  };
}

export type LayoutModule = ReturnType<typeof useLayout>;
