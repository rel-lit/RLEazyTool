import type { AnalysisSummary } from "../../api/client";

export type RecipeDetailSummary = {
  readonly recipe_name: string;
  readonly label?: string;
  readonly line: string;
  readonly kind: "craft" | "extract" | "unknown";
};

/** 与后端 build_layout_analysis_meta 对齐的只读分析视图 */
export interface NormalizedAnalysisSummary {
  readonly declared_outputs: readonly string[];
  readonly effective_terminals: readonly string[];
  readonly demoted_outputs: readonly string[];
  readonly analysis_items: readonly string[];
  readonly pseudo_pure_sources: readonly string[];
  readonly recipe_assignments: Readonly<Record<string, string>>;
  readonly recipe_details: Readonly<Record<string, RecipeDetailSummary>>;
  readonly impossible: boolean;
  readonly max_layer?: number;
}

/** 列表桶内排序键（tier 越小越靠前） */
export interface ItemListSortKey {
  readonly tier: number;
  readonly layer: number;
  readonly rank: number;
  readonly rankFrac: number;
  readonly label: string;
  readonly name: string;
}

export type { AnalysisSummary };
