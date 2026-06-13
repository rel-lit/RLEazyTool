import type { LayoutRequest, LayoutResponse } from "../api/client";
import type { NodePositionMap } from "../domains/layout/useLayout";
import { DEFAULT_LAYOUT_OPTIONS } from "../../app/config";
import type { SelectionModule } from "../domains/selection/useSelection";

export type LayoutSnapshotUpsert = {
  request: LayoutRequest;
  response: LayoutResponse;
  user_positions: NodePositionMap;
  layout_key?: string | null;
};

export interface SnapshotBuildContext {
  layout: LayoutResponse | null;
  /** 产生当前画布 layout 的那份 request；不得用「即将重算」的 selection */
  boundRequest: LayoutRequest | null;
  readCanvasPositions: () => NodePositionMap;
}

export function buildLayoutRequest(
  selection: SelectionModule,
  catalogMode: "progress" | "full"
): LayoutRequest {
  return {
    targets: selection.selectedTargets.value.map((item) => ({ item })),
    supply_mode: selection.supplyMode.value,
    supplied_items: [...selection.suppliedItems.value],
    forbidden_items: [...selection.forbiddenItems.value],
    catalog_mode: catalogMode,
    layout_options: { ...DEFAULT_LAYOUT_OPTIONS },
  };
}

function positionsFromResponse(layout: LayoutResponse): NodePositionMap {
  return Object.fromEntries(
    layout.nodes.map((n) => [n.id, { x: n.position.x, y: n.position.y }])
  );
}

export function resolveUserPositions(ctx: SnapshotBuildContext): NodePositionMap {
  const canvas = ctx.readCanvasPositions();
  if (Object.keys(canvas).length > 0) {
    return canvas;
  }
  if (ctx.layout) {
    return positionsFromResponse(ctx.layout);
  }
  return {};
}

export function buildLayoutSnapshot(ctx: SnapshotBuildContext): LayoutSnapshotUpsert | null {
  const layout = ctx.layout;
  if (!layout?.nodes?.length || layout.analysis?.impossible) {
    return null;
  }
  if (!ctx.boundRequest) {
    return null;
  }
  return {
    request: ctx.boundRequest,
    response: layout,
    user_positions: resolveUserPositions(ctx),
  };
}

export function mergeSnapshotIntoLayout(
  response: LayoutResponse,
  userPositions: NodePositionMap
): LayoutResponse {
  if (!Object.keys(userPositions).length) {
    return response;
  }
  return {
    ...response,
    nodes: response.nodes.map((n) => ({
      ...n,
      position: userPositions[n.id] ?? n.position,
    })),
  };
}
