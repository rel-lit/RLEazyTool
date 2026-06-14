/** 画布 UI 区内的交互目标（不含业务含义） */

export type CanvasRegionTarget =
  | { kind: "node"; id: string }
  | { kind: "edge"; id: string }
  | { kind: "pane" };

/** 画布区向编排层发出的语义事件（与 UiControl 的 primary 对齐） */
export type CanvasRegionEmit = {
  (event: "primary", target: CanvasRegionTarget): void;
};

export interface CanvasHighlightResolver<THighlight> {
  resolveNode: (nodeId: string) => THighlight;
  resolveEdge: (edgeId: string) => THighlight | null;
}
