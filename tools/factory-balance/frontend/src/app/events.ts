import type { FactorioStatus, ItemInfo, LayoutResponse, PurgeCacheResponse } from "../api/client";

export interface CatalogPayload {
  manufacture_items: ItemInfo[];
  supply_items: ItemInfo[];
}

export type AppEvent =
  | { type: "BootstrapStarted" }
  | { type: "BootstrapComplete" }
  | { type: "SessionRefreshed"; status: FactorioStatus }
  | { type: "ImportStarted"; saveKey: string }
  | { type: "ImportFailed"; message: string }
  | {
      type: "ProgressChanged";
      saveKey: string;
      catalog: CatalogPayload;
      warnings: string[];
      enabledCount: number;
      progressStale?: boolean;
    }
  | { type: "ProgressCleared" }
  | { type: "CatalogModeChanged"; mode: "progress" | "full" }
  | {
      type: "CatalogLoaded";
      mode: "progress" | "full";
      catalog: CatalogPayload;
      progressLoaded: boolean;
      progressStale?: boolean;
      activeSaveKey?: string | null;
      hasRecipePack: boolean;
    }
  | { type: "CatalogLoadFailed"; message: string }
  | { type: "SelectionChanged"; reason: "user-toggle" | "pruned" | "reset" }
  | { type: "LayoutInvalidated"; reason: string }
  | { type: "LayoutComputeStarted"; resetPositions?: boolean }
  | { type: "LayoutComputed"; layout: LayoutResponse }
  | { type: "LayoutRestoredFromHistory"; layout: LayoutResponse }
  | { type: "LayoutComputeFailed"; message: string }
  | { type: "CachePurgeStarted" }
  | { type: "CachePurged"; result: PurgeCacheResponse; progressStillLoaded: boolean };

type AppEventListener = (event: AppEvent) => void;

export interface AppEventBus {
  emit(event: AppEvent): void;
  on(type: AppEvent["type"], listener: AppEventListener): () => void;
}

export function createAppEventBus(): AppEventBus {
  const listeners = new Map<AppEvent["type"], Set<AppEventListener>>();

  function on(type: AppEvent["type"], listener: AppEventListener): () => void {
    if (!listeners.has(type)) listeners.set(type, new Set());
    listeners.get(type)!.add(listener);
    return () => listeners.get(type)?.delete(listener);
  }

  function emit(event: AppEvent): void {
    listeners.get(event.type)?.forEach((fn) => fn(event));
  }

  return { emit, on };
}
