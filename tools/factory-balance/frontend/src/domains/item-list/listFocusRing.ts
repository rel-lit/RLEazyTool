import type { LayoutFocusView } from "../layout-inspection";

/** 画布钉选子树 / 链涉及物品是否在列表上显示圈选 */
export function hasListFocusRing(
  itemName: string,
  focusView: LayoutFocusView | null | undefined
): boolean {
  if (!focusView?.pinned) return false;
  return focusView.itemNames.has(itemName);
}
