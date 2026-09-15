import type { AnalyzeResponse } from "@/lib/types";
import PathCard from "@/components/PathCard";

interface ResultsCardsProps {
  data: AnalyzeResponse;
}

export default function ResultsCards({ data }: ResultsCardsProps) {
  const pathScores = [
    data.build_analysis.score,
    data.partner_analysis.score,
    data.acquire_analysis.score,
  ];
  const maxScore = Math.max(...pathScores);
  const recommendedPath =
    pathScores.indexOf(maxScore) === 0
      ? "Build"
      : pathScores.indexOf(maxScore) === 1
        ? "Partner"
        : "Acquire";

  const isCloseCall =
    Math.abs(pathScores[0] - pathScores[1]) <= 1.0 ||
    Math.abs(pathScores[1] - pathScores[2]) <= 1.0 ||
    Math.abs(pathScores[0] - pathScores[2]) <= 1.0;

  return (
    <div
      className="w-full max-w-6xl mx-auto space-y-8"
      data-testid="results-cards"
    >
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-crustdata-light">
          Strategy Analysis: {data.my_company} — {data.capability}
        </h1>
        <div className="flex items-center justify-center gap-3">
          <span className="px-4 py-1 bg-crustdata-blue/10 text-crustdata-blue rounded-full text-sm font-medium">
            Recommended: {recommendedPath}
          </span>
          {isCloseCall && (
            <span className="px-4 py-1 bg-crustdata-accent/10 text-crustdata-accent rounded-full text-sm font-medium">
              Close call — consider alternatives
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:gap-8 md:grid-cols-2 lg:grid-cols-3">
        <PathCard analysis={data.build_analysis} />
        <PathCard analysis={data.partner_analysis} />
        <PathCard analysis={data.acquire_analysis} />
      </div>
    </div>
  );
}
