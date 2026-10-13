import { describe, expect, it } from "vitest";
import { getRecommendation, isScored } from "@/lib/score";
import type { AnalyzeResponse, PathAnalysis } from "@/lib/types";

function path(name: string, score: number): PathAnalysis {
  return {
    path: name,
    score,
    reasoning: `${name} reasoning`,
    timeline_months: null,
    estimated_cost_usd: null,
    candidates: [],
  };
}

function response(
  build: number,
  partner: number,
  acquire: number,
): AnalyzeResponse {
  return {
    my_company: "Retool",
    capability: "Real-time analytics",
    build_analysis: path("build", build),
    partner_analysis: path("partner", partner),
    acquire_analysis: path("acquire", acquire),
  };
}

describe("isScored", () => {
  it("treats zero as unscored, because the rubric drops criteria it has no data for", () => {
    expect(isScored(path("build", 0))).toBe(false);
  });

  it("treats any positive score as scored", () => {
    expect(isScored(path("build", 0.1))).toBe(true);
  });
});

describe("getRecommendation", () => {
  it("ranks the paths highest first and leads with the winner", () => {
    const { leader, ranked } = getRecommendation(response(6.2, 8.4, 7.1));

    expect(leader?.path).toBe("partner");
    expect(ranked.map((p) => p.path)).toEqual(["partner", "acquire", "build"]);
  });

  it("excludes every alternative from the leader slot", () => {
    const { leader, alternatives } = getRecommendation(response(6.2, 8.4, 7.1));

    expect(alternatives).toHaveLength(2);
    expect(alternatives).not.toContain(leader);
  });

  it("flags a close call when the runner-up is within a point", () => {
    expect(getRecommendation(response(7.6, 8.4, 2.0)).isCloseCall).toBe(true);
    expect(getRecommendation(response(5.0, 8.4, 2.0)).isCloseCall).toBe(false);
  });

  it("returns no leader when nothing could be scored", () => {
    const { leader, isCloseCall } = getRecommendation(response(0, 0, 0));

    expect(leader).toBeNull();
    expect(isCloseCall).toBe(false);
  });

  it("ignores unscored paths when picking the leader", () => {
    const { leader } = getRecommendation(response(0, 0, 1.7));

    expect(leader?.path).toBe("acquire");
  });
});
