import type { PathAnalysis } from "@/lib/types";
import ScoreProgress from "@/components/ScoreProgress";
import CandidateTable from "@/components/CandidateTable";

interface PathCardProps {
  analysis: PathAnalysis;
}

const PATH_META: Record<string, { label: string; color: string; bg: string }> = {
  build: { label: "Build", color: "text-crustdata-blue", bg: "bg-crustdata-blue/10" },
  partner: { label: "Partner", color: "text-emerald-400", bg: "bg-emerald-500/10" },
  acquire: { label: "Acquire", color: "text-amber-400", bg: "bg-amber-500/10" },
};

export default function PathCard({ analysis }: PathCardProps) {
  const meta = PATH_META[analysis.path] || PATH_META.build;
  const hasCandidates = analysis.candidates && analysis.candidates.length > 0;

  return (
    <div
      className={`rounded-xl border border-gray-700/50 bg-crustdata-dark/40 shadow-xl transition-all duration-300 hover:shadow-crustdata-blue/20`}
      data-testid={`path-card-${analysis.path}`}
    >
      <div className={`p-6 border-b border-gray-700/50 ${meta.bg}`}>
        <div className="flex items-center justify-between">
          <h2 className={`text-2xl font-bold ${meta.color}`}>
            {meta.label}
          </h2>
          <span
            className={`text-2xl font-bold ${meta.color} bg-crustdata-dark/30 px-4 py-2 rounded-lg`}
          >
            {analysis.score.toFixed(1)}/10
          </span>
        </div>
      </div>

      <div className="p-6 space-y-5">
        <ScoreProgress
          score={analysis.score}
          label="Path Score"
          size="md"
        />

        <p className="text-crustdata-light/80 text-sm leading-relaxed">
          {analysis.reasoning}
        </p>

        {analysis.timeline_months !== null && (
          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="bg-crustdata-dark/30 rounded-lg p-4 border border-gray-700/30">
              <span className="text-xs font-medium text-crustdata-light/60 uppercase">
                Timeline
              </span>
              <p className="text-lg font-semibold text-crustdata-light mt-1">
                {analysis.timeline_months} months
              </p>
            </div>
            <div className="bg-crustdata-dark/30 rounded-lg p-4 border border-gray-700/30">
              <span className="text-xs font-medium text-crustdata-light/60 uppercase">
                Est. Cost
              </span>
              <p className="text-lg font-semibold text-crustdata-light mt-1">
                ${analysis.estimated_cost_usd?.toLocaleString() || "—"}
              </p>
            </div>
          </div>
        )}

        {hasCandidates && (
          <div className="pt-2">
            <CandidateTable
              candidates={analysis.candidates}
              path={analysis.path}
            />
          </div>
        )}
      </div>
    </div>
  );
}
