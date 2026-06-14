/** 列表项—布局关联标记：透孔圆环 + 圈内语义填充色 */
export type ListLayoutMarkKind = "none" | "hollow-sphere";

export type ItemListSide = "target" | "supply";

export interface ListLayoutMark {
  kind: ListLayoutMarkKind;
  /** 圈内填充（与画布节点底色同源或专用规则） */
  fill?: string;
  ringColor?: string;
  ringStyle?: "solid" | "dashed";
  ringWidth?: string;
}

export const LIST_LAYOUT_MARK_NONE: ListLayoutMark = { kind: "none" };
