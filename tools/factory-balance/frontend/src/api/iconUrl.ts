const ICON_ASSET_VERSION = "2";

export function resolveItemIconUrl(slug: string | null | undefined): string | null {
  if (!slug) return null;
  return `/api/v1/static/icons/${slug}.png?v=${ICON_ASSET_VERSION}`;
}
