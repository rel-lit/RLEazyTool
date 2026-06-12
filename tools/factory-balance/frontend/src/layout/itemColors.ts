/** 按物料名生成稳定、可区分的边颜色 */
const PALETTE = [
  "#58a6ff",
  "#3fb950",
  "#f0883e",
  "#bc8cff",
  "#ff7b72",
  "#79c0ff",
  "#d2a8ff",
  "#ffa657",
  "#56d364",
  "#e3b341",
];

export function itemEdgeColor(item: string): string {
  let hash = 0;
  for (let i = 0; i < item.length; i++) {
    hash = (hash * 31 + item.charCodeAt(i)) >>> 0;
  }
  return PALETTE[hash % PALETTE.length];
}
