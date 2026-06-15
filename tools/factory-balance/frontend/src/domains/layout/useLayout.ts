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

function requestKey(body: LayoutRequest): string {
  // recipe_assignments 是本次分析的用户覆盖，不应参与 key；否则确认后 key 会变
  return JSON.stringify({
    targets: body.targets,
    supply_mode: body.supply_mode,
    supplied_items: body.supplied_items,
    forbidden_items: body.forbidden_items,
    catalog_mode: body.catalog_mode,
    layout_options: body.layout_options,
  });
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

  // 当前分析集的配方选择缓存：同一次请求内复用，换分析集后丢弃
  const cachedRequestKey = ref<string | null>(null);
  const cachedAssignments = ref<Record<string, string>>({});

  const boundRequest = boundRequestRef;

  const analysisWarnings = computed(() => layout.value?.warnings ?? []);

  function clearAssignmentCache(): void {
    cachedRequestKey.value = null;
    cachedAssignments.value = {};
  }

  function reset(): void {
    layout.value = null;
    error.value = "";
    stale.value = false;
    boundRequestRef.value = null;
    pendingRecipePreview.value = null;
    clearAssignmentCache();
  }

  function invalidate(reason: string): void {
    if (layout.value) stale.value = true;
    error.value = "";
    clearAssignmentCache();
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
    const key = requestKey(body);

    // 外部显式传入的覆盖优先级最高，且会清空缓存
    if (recipeAssignments && Object.keys(recipeAssignments).length > 0) {
      body.recipe_assignments = recipeAssignments;
      clearAssignmentCache();
      await resolveAndCompute(body, recipeAssignments, true);
      return;
    }

    // 同一分析集：复用已确认的选择，不再弹窗
    if (cachedRequestKey.value === key && Object.keys(cachedAssignments.value).length > 0) {
      body.recipe_assignments = { ...cachedAssignments.value };
      await resolveAndCompute(body, cachedAssignments.value, true);
      return;
    }

    // 新分析集：清空缓存并进入 preview
    clearAssignmentCache();
    await resolveAndCompute(body, {}, false);
  }

  async function resolveAndCompute(
    body: LayoutRequest,
    confirmedAssignments: Record<string, string>,
    skipPreview = false
  ): Promise<void> {
    try {
      if (!skipPreview) {
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

    // 缓存：仅用于当前这次分析集
    cachedRequestKey.value = requestKey(body);
    cachedAssignments.value = merged;

    pendingRecipePreview.value = null;
    loading.value = true;
    // 用户确认后直接计算，不再级联 preview，避免死循环
    void resolveAndCompute(body, merged, true);
  }

  function cancelRecipePreview(): void {
    pendingRecipePreview.value = null;
    loading.value = false;
    stale.value = false;
    clearAssignmentCache();
    bus.emit({ type: "LayoutComputeCancelled" });
  }

  function applyLayout(data: LayoutResponse, request?: LayoutRequest): void {
    layout.value = data;
    error.value = "";
    stale.value = false;
    pendingRecipePreview.value = null;
    if (request) {
      boundRequestRef.value = request;
      cachedRequestKey.value = requestKey(request);
      cachedAssignments.value = request.recipe_assignments
        ? { ...request.recipe_assignments }
        : {};
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
