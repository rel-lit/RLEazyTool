/** 画布坐标读取桥：LayoutCanvas 注册，Layer P 读取（避免 store 依赖 Vue Flow） */

import type { NodePositionMap } from "../domains/layout/useLayout";

let readPositions: (() => NodePositionMap) | null = null;

export function registerCanvasPositionReader(fn: () => NodePositionMap): void {
  readPositions = fn;
}

export function unregisterCanvasPositionReader(): void {
  readPositions = null;
}

export function readCanvasNodePositions(): NodePositionMap {
  return readPositions?.() ?? {};
}
