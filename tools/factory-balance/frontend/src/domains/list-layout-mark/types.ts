/** 列表项—布局关联标记：透孔圆环 + 圈内语义填充色 */
export type ListLayoutMarkKind = "none" | "hollow-sphere";

export type ItemListSide = "target" | "supply";

/** 圆环线框变体（细铁环为 default；语义色只在圈内 fill） */
export type ListLayoutMarkRing = "default" | "demoted" | "forbidden" | "assumed";

export interface ListLayoutMark {
  kind: ListLayoutMarkKind;
  /** 圈内填充；transparent 表示空环（如禁止供给） */
  fill?: string;
  ring?: ListLayoutMarkRing;
}

export const LIST_LAYOUT_MARK_NONE: ListLayoutMark = { kind: "none" };
