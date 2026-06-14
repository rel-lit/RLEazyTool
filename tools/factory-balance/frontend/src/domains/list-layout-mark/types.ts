/** 列表项—布局关联标记：透孔 + 双层（圈内 fill / 外环 rim） */
export type ListLayoutMarkKind = "none" | "hollow-sphere";

export type ItemListSide = "target" | "supply";

/**
 * 外环 rim 语义（统一禁止环质感：rim 在 ::after，fill 在 ::before）。
 * 每种对应 pipeline 的一类判定。
 */
export type ListLayoutMarkRing =
  | "terminal"
  | "intermediate"
  | "demoted"
  | "pure-solid"
  | "pure-world"
  | "assumed"
  | "forbidden"
  | "extract";

export interface ListLayoutMark {
  kind: ListLayoutMarkKind;
  /** 圈内填充；transparent = 空芯（禁止供给） */
  fill?: string;
  ring: ListLayoutMarkRing;
}

export const LIST_LAYOUT_MARK_NONE: ListLayoutMark = { kind: "none", ring: "intermediate" };
