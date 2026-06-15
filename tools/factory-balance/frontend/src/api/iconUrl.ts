export function resolveItemIconUrl(slug: string | null | undefined): string | null {
  if (!slug) return null;
  return `/api/v1/static/icons/${slug}.png`;
}
