import type { AnalysisSummary } from "../../api/client";
import type { NormalizedAnalysisSummary } from "./types";

type RawAnalysis = AnalysisSummary & {
  terminals?: readonly string[];
  pseudo_external?: readonly string[];
};

/** 兼容旧快照：terminals / pseudo_external → 规范字段 */
export function normalizeAnalysisSummary(
  analysis: AnalysisSummary | undefined | null
): NormalizedAnalysisSummary | null {
  if (!analysis) return null;

  const raw = analysis as RawAnalysis;
  const declared = raw.declared_outputs ?? [];
  const effective = raw.effective_terminals ?? raw.terminals ?? [];
  const effectiveSet = new Set(effective);
  const demoted =
    raw.demoted_outputs ?? declared.filter((name) => !effectiveSet.has(name));
  const pseudo = raw.pseudo_pure_sources ?? raw.pseudo_external ?? [];

  return {
    declared_outputs: declared,
    effective_terminals: effective,
    demoted_outputs: demoted,
    analysis_items: raw.analysis_items ?? [],
    pseudo_pure_sources: pseudo,
    recipe_assignments: { ...(raw.recipe_assignments ?? {}) },
    recipe_details: { ...(raw.recipe_details ?? {}) },
    impossible: Boolean(raw.impossible),
    max_layer: raw.max_layer,
  };
}
