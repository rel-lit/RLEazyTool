/** 画布 primary 选中的检视对象（节点 / 边互斥，与 hover 分离） */
export type InspectionTarget =
  | { readonly kind: "node"; readonly id: string }
  | { readonly kind: "edge"; readonly id: string };

export type LayoutFocusMode =
  | "idle"
  | "node-subtree"
  | "sbto-chain"
  | "belt-edge";

/** 钉选后供列表圈选等只读消费的焦点视图 */
export interface LayoutFocusView {
  readonly mode: LayoutFocusMode;
  readonly itemNames: ReadonlySet<string>;
  readonly sbtoItem: string | null;
  readonly pinned: true;
}

export interface InspectionPanelSection {
  readonly heading: string;
  readonly lines: readonly string[];
  readonly bullets?: readonly string[];
}

/** 信息栏右栏统一模型（节点 / 边互斥） */
export interface InspectionPanelModel {
  readonly kind: "node" | "edge";
  /** 检视类型徽章：节点 / 边 / SBTO边 */
  readonly badge: InspectionBadge;
  readonly title: string;
  readonly subtitle?: string;
  readonly sections: readonly InspectionPanelSection[];
}

export type InspectionBadge = "节点" | "边" | "SBTO边";
