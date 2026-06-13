/** SBTO 优先级徽章：稳定哈希色相 + 同布局内防碰撞 */

const HUE_MIN = 18;
const HUE_MAX = 328;
const MIN_HUE_DELTA = 20;
const BADGE_SAT = 72;
const BADGE_LIGHT = 48;

function hashItem(item: string): number {
  let hash = 0;
  for (let i = 0; i < item.length; i++) {
    hash = (hash * 31 + item.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function hashHue(item: string): number {
  const t = (hashItem(item) % 10_000) / 10_000;
  return HUE_MIN + t * (HUE_MAX - HUE_MIN);
}

function hueDistance(a: number, b: number): number {
  const d = Math.abs(a - b);
  return Math.min(d, 360 - d);
}

function hslToHex(h: number, s: number, l: number): string {
  const hh = ((h % 360) + 360) % 360;
  const ss = s / 100;
  const ll = l / 100;
  const c = (1 - Math.abs(2 * ll - 1)) * ss;
  const x = c * (1 - Math.abs(((hh / 60) % 2) - 1));
  const m = ll - c / 2;
  let r = 0;
  let g = 0;
  let b = 0;
  if (hh < 60) {
    r = c;
    g = x;
  } else if (hh < 120) {
    r = x;
    g = c;
  } else if (hh < 180) {
    g = c;
    b = x;
  } else if (hh < 240) {
    g = x;
    b = c;
  } else if (hh < 300) {
    r = x;
    b = c;
  } else {
    r = c;
    b = x;
  }
  const toByte = (v: number) =>
    Math.round((v + m) * 255)
      .toString(16)
      .padStart(2, "0");
  return `#${toByte(r)}${toByte(g)}${toByte(b)}`;
}

/** 同布局内为每条 SBTO 链分配可辨徽章色（链 stroke 不变） */
export function assignSbtoBadgeColors(items: string[]): Map<string, string> {
  const unique = [...new Set(items)].sort();
  const used: number[] = [];
  const map = new Map<string, string>();

  for (const item of unique) {
    let hue = hashHue(item);
    for (let attempt = 0; attempt < 48; attempt++) {
      if (used.every((u) => hueDistance(u, hue) >= MIN_HUE_DELTA)) {
        used.push(hue);
        map.set(item, hslToHex(hue, BADGE_SAT, BADGE_LIGHT));
        break;
      }
      hue = (hue + MIN_HUE_DELTA) % 360;
    }
    if (!map.has(item)) {
      map.set(item, hslToHex(hue, BADGE_SAT, BADGE_LIGHT));
    }
  }

  return map;
}

/** @deprecated 仅兼容；新代码用 assignSbtoBadgeColors */
export function itemEdgeColor(item: string): string {
  return hslToHex(hashHue(item), BADGE_SAT, BADGE_LIGHT);
}
