import type { LayoutRequest, LayoutResponse } from "../../api/client";
import {
  getLayoutHistory,
  upsertLayoutSnapshot,
  upsertLayoutSnapshotBeacon,
  type LayoutSnapshotDetail,
} from "../../api/client";
import type { AppEventBus } from "../../app/events";
import {
  buildLayoutSnapshot,
  mergeSnapshotIntoLayout,
  type LayoutSnapshotUpsert,
} from "./layoutSnapshot";

export interface LayoutPersistenceDeps {
  bus: AppEventBus;
  getLayout: () => LayoutResponse | null;
  getBoundRequest: () => LayoutRequest | null;
  readCanvasPositions: () => Record<string, { x: number; y: number }>;
}

/** Layer P 存储逻辑：组装快照 + 调用 API upsert（不含触发时机） */
export function createLayoutPersistence(deps: LayoutPersistenceDeps) {
  let pageLeaveHookInstalled = false;

  function currentSnapshot(): LayoutSnapshotUpsert | null {
    return buildLayoutSnapshot({
      layout: deps.getLayout(),
      boundRequest: deps.getBoundRequest(),
      readCanvasPositions: deps.readCanvasPositions,
    });
  }

  async function saveBeforeRecompute(): Promise<boolean> {
    const snap = currentSnapshot();
    if (!snap) {
      return false;
    }
    try {
      await upsertLayoutSnapshot(snap);
      deps.bus.emit({ type: "LayoutSnapshotSaved", reason: "before-recompute" });
      return true;
    } catch {
      return false;
    }
  }

  function saveOnPageLeave(): void {
    const snap = currentSnapshot();
    if (!snap) return;
    upsertLayoutSnapshotBeacon(snap);
  }

  /** 关页、刷新、浏览器导航离开；不含 Vue 组件卸载或选项变动 */
  function installPageLeaveHook(): void {
    if (pageLeaveHookInstalled || typeof window === "undefined") return;
    pageLeaveHookInstalled = true;
    window.addEventListener("beforeunload", saveOnPageLeave);
    window.addEventListener("pagehide", saveOnPageLeave);
  }

  async function loadDetail(
    id: number
  ): Promise<{ layout: LayoutResponse; request: LayoutRequest } | null> {
    const detail: LayoutSnapshotDetail = await getLayoutHistory(id);
    return {
      layout: layoutFromDetail(detail),
      request: detail.request as LayoutRequest,
    };
  }

  function layoutFromDetail(detail: LayoutSnapshotDetail): LayoutResponse {
    const response = detail.response as LayoutResponse;
    const positions = detail.user_positions as Record<string, { x: number; y: number }>;
    return mergeSnapshotIntoLayout(response, positions);
  }

  return {
    saveBeforeRecompute,
    installPageLeaveHook,
    loadDetail,
    layoutFromDetail,
  };
}

export type LayoutPersistence = ReturnType<typeof createLayoutPersistence>;
