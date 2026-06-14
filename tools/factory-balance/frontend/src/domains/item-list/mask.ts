import type { ItemInfo } from "../../api/client";

/** 搜索遮罩：仅决定 UI 可见性，不修改 session / selection 状态 */
export function applyListMask(items: readonly ItemInfo[], query: string): ItemInfo[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return items as ItemInfo[];
  return items.filter(
    (i) => i.label.toLowerCase().includes(needle) || i.name.toLowerCase().includes(needle)
  );
}
