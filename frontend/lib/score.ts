import type { AnalyzeResponse, PathAnalysis } from "@/lib/types";

export const MAX_SCORE = 10;

/**
 * Two paths within this many points of each other are not meaningfully
 * separated by the rubric, so the UI says so instead of implying precision
 * the scoring engine did not claim.
 */
export const CLOSE_CALL_MARGIN = 1.0;

/**
 * rubric.yaml excludes criteria with missing data and renormalises the
 * remaining weights, so a scored path is never 0. A 0 here means the engine
 * had nothing to score with, which is a different statement from "scored
 * badly" and has to read differently in the UI.
 */
export function isScored(analysis: PathAnalysis): boolean {
  return Number.isFinite(analysis.score) && analysis.score > 0;
}

export function formatScore(score: number): string {
  return score.toFixed(1);
}

export const PATH_LABELS: Record<string, string> = {
  build: "Build",
  partner: "Partner",
  acquire: "Acquire",
};

export function pathLabel(path: string): string {
  return PATH_LABELS[path] ?? path.charAt(0).toUpperCase() + path.slice(1);
}

export interface Recommendation {
  /** Highest scoring path, or null when nothing could be scored. */
  leader: PathAnalysis | null;
  /** Every other path, highest first. */
  alternatives: PathAnalysis[];
  /** All three in rank order, unscored paths last. */
  ranked: PathAnalysis[];
  /** Runner-up sits within CLOSE_CALL_MARGIN of the leader. */
  isCloseCall: boolean;
}

export function getRecommendation(data: AnalyzeResponse): Recommendation {
  const ranked = [
    data.build_analysis,
    data.partner_analysis,
    data.acquire_analysis,
  ].sort((a, b) => b.score - a.score);

  const scored = ranked.filter(isScored);
  const leader = scored[0] ?? null;

  return {
    leader,
    alternatives: leader ? ranked.filter((p) => p !== leader) : ranked,
    ranked,
    isCloseCall:
      scored.length > 1 && scored[0].score - scored[1].score <= CLOSE_CALL_MARGIN,
  };
}
