/** 列表项—布局关联标记样式（v1 透孔圆环；圈内透出 chip 后方背景） */
export type ListLayoutMarkKind = "none" | "hollow-sphere";

export interface ListLayoutMark {
  kind: ListLayoutMarkKind;
}

export const LIST_LAYOUT_MARK_NONE: ListLayoutMark = { kind: "none" };
