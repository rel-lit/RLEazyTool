/** 列表项—布局关联标记样式（v1 仅镂空球；后续可扩展终端/纯原料/layer 等） */
export type ListLayoutMarkKind = "none" | "hollow-sphere";

export interface ListLayoutMark {
  kind: ListLayoutMarkKind;
}

export const LIST_LAYOUT_MARK_NONE: ListLayoutMark = { kind: "none" };
