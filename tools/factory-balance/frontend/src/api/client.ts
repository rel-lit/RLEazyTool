import axios from "axios";

const client = axios.create({ baseURL: "/api/v1" });

export interface LayoutTarget {
  item: string;
  rate_per_minute?: number | null;
}

export interface LayoutRequest {
  targets: LayoutTarget[];
  supply_mode: "raw" | "direct";
  supplied_items: string[];
  forbidden_items: string[];
  catalog_mode: "progress" | "full";
  layout_options: {
    primary_direction: "left-to-right" | "top-to-bottom";
  buffer_recommendation: boolean;
  };
  /** 重算前画布坐标快照，不参与算法，仅写入历史 request */
  user_layout_before?: {
    node_positions: Record<string, { x: number; y: number }>;
    captured_at?: string | null;
  };
}

export interface LayoutNode {
  id: string;
  type: string;
  item: string;
  label: string;
  layer: number;
  position: { x: number; y: number };
  recipe?: string | null;
  meta?: {
    role?: string;
    supply_kind?: string;
    is_pure_source?: boolean;
    placeholder?: string;
  };
}

export interface LayoutEdge {
  id: string;
  type: string;
  item: string;
  label: string;
  from: string;
  to: string;
  tap_index?: number | null;
  self_balance?: boolean;
  rule?: string | null;
  note?: string | null;
}

export interface TapOrderEntry {
  item: string;
  label: string;
  order: string[];
  order_labels: string[];
  rule: string;
  explanation: string;
}

export interface AnalysisSummary {
  effective_terminals: string[];
  declared_outputs: string[];
  demoted_outputs: string[];
  pseudo_pure_sources: string[];
  true_pure_sources: string[];
  analysis_items: string[];
  recipe_assignments: Record<string, string>;
  impossible: boolean;
}

export interface LayoutResponse {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  product_edges: LayoutEdge[];
  hidden_edges: LayoutEdge[];
  tap_orders: TapOrderEntry[];
  warnings: string[];
  analysis: AnalysisSummary;
  layout_direction?: "left-to-right" | "top-to-bottom";
  history_id?: number | null;
  extensions: Record<string, unknown>;
}

export interface LayoutHistoryEntry {
  id: number;
  save_key: string | null;
  env_key: string | null;
  catalog_mode: string;
  supply_mode: string;
  target_summary: string;
  target_count: number;
  node_count: number;
  edge_count: number;
  tap_count: number;
  created_at: string;
}

export interface LayoutHistoryDetail extends LayoutHistoryEntry {
  request: LayoutRequest;
  response: LayoutResponse;
}

export interface ItemInfo {
  name: string;
  label: string;
  is_raw: boolean;
  expansion?: string | null;
}

export interface SaveInfo {
  name: string;
  path: string;
  modified_at: string;
  is_last_played: boolean;
  game_version?: string | null;
  has_cached_progress?: boolean;
  needs_reimport?: boolean;
}

export interface FactorioStatus {
  user_data_dir: string;
  saves_dir: string;
  executable: string | null;
  executable_source?: string | null;
  save_count: number;
  last_played_save: string | null;
  session_updated_at: string | null;
  database_source: string;
  progress_loaded: boolean;
  progress_stale?: boolean;
  active_save_key?: string | null;
  enabled_recipe_count: number;
  craftable_item_count: number;
  has_recipe_pack: boolean;
  pack_count: number;
}

export interface PurgeCacheResponse {
  ok: boolean;
  deleted_packs: number;
  deleted_progress: number;
  legacy_files_removed: string[];
}

export interface ItemCatalogResponse {
  all_items: ItemInfo[];
  manufacture_items: ItemInfo[];
  supply_items: ItemInfo[];
  database_source: string;
  progress_loaded: boolean;
  progress_stale?: boolean;
  active_save_key?: string | null;
  catalog_mode: "progress" | "full";
  has_recipe_pack: boolean;
  pack_count: number;
}

export interface ProgressResponse {
  ok: boolean;
  save?: string | null;
  researched_technology_count: number;
  enabled_recipe_count: number;
  craftable_items: ItemInfo[];
  manufacture_items?: ItemInfo[];
  supply_items?: ItemInfo[];
  warnings: string[];
  database_source: string;
  progress_stale?: boolean;
  reexported?: boolean;
}

export async function searchItems(q = "", craftableOnly = false): Promise<ItemInfo[]> {
  const { data } = await client.get("/recipes/search", {
    params: { q, craftable_only: craftableOnly },
  });
  return data.items;
}

export async function computeLayout(body: LayoutRequest): Promise<LayoutResponse> {
  const { data } = await client.post("/layout/compute", body, { timeout: 120_000 });
  return data;
}

export async function listLayoutHistory(limit = 50): Promise<LayoutHistoryEntry[]> {
  const { data } = await client.get("/layout/history", { params: { limit } });
  return data;
}

export async function getLayoutHistory(id: number): Promise<LayoutHistoryDetail> {
  const { data } = await client.get(`/layout/history/${id}`);
  return data;
}

export async function deleteLayoutHistory(id: number): Promise<void> {
  await client.delete(`/layout/history/${id}`);
}

export async function clearLayoutHistory(): Promise<number> {
  const { data } = await client.delete("/layout/history");
  return data.deleted as number;
}

export async function getFactorioStatus(): Promise<FactorioStatus> {
  const { data } = await client.get("/factorio/status");
  return data;
}

export async function listSaves(): Promise<SaveInfo[]> {
  const { data } = await client.get("/factorio/saves");
  return data;
}

export async function fetchItemCatalog(mode: "progress" | "full" = "progress"): Promise<ItemCatalogResponse> {
  const { data } = await client.get("/items/catalog", { params: { mode } });
  return data;
}

export async function loadProgress(save: string, reexport = false): Promise<ProgressResponse> {
  const { data } = await client.post("/factorio/load-progress", {
    save,
    reexport,
  });
  return data;
}

export async function refreshPrototypes(): Promise<{ ok: boolean; warnings: string[] }> {
  const { data } = await client.post("/factorio/refresh-prototypes");
  return { ok: data.ok, warnings: data.warnings ?? [] };
}

export async function purgeCache(keepActive = true): Promise<PurgeCacheResponse> {
  const { data } = await client.post("/factorio/purge-cache", null, {
    params: { keep_active: keepActive },
  });
  return data;
}
