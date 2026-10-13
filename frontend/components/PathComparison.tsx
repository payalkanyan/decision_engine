import type { PathAnalysis } from "@/lib/types";
import { isScored, pathLabel } from "@/lib/score";
import ScoreMeter from "@/components/ScoreMeter";

interface PathComparisonProps {
  ranked: PathAnalysis[];
  leader: PathAnalysis | null;
}

/**
 * All three paths as rows rather than three identical cards, so rank is read
 * top to bottom instead of inferred by comparing numbers across columns.
 */
export default function PathComparison({
  ranked,
  leader,
}: PathComparisonProps) {
  return (
    <section className="pt-24">
      <h3
        data-reveal
        className="text-3xl font-semibold tracking-[-0.03em] lg:text-[2.75rem]"
      >
        All three paths
      </h3>

      <div className="mt-14 border-t border-line">
        {ranked.map((analysis) => {
          const isLeader = analysis === leader;
          return (
            <article
              key={analysis.path}
              data-reveal
              className="grid gap-6 border-b border-line py-10 lg:grid-cols-12 lg:gap-10"
              data-testid={`path-row-${analysis.path}`}
            >
              <h4
                className={`text-3xl font-medium tracking-[-0.03em] lg:col-span-3 ${
                  isLeader ? "text-accent" : "text-text"
                }`}
              >
                {pathLabel(analysis.path)}
              </h4>

              <div className="lg:col-span-3">
                <ScoreMeter
                  score={analysis.score}
                  scored={isScored(analysis)}
                  emphasis={isLeader}
                />
              </div>

              <div className="max-w-[58ch] space-y-4 lg:col-span-6">
                {/* The leader's reasoning is already printed in full directly
                    above, so repeating it here is noise. */}
                {isLeader ? (
                  <p className="text-sm text-faint">
                    Recommended. Reasoning above.
                  </p>
                ) : (
                  <p className="leading-relaxed text-muted">
                    {analysis.reasoning}
                  </p>
                )}
                <PathMeta analysis={analysis} />
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function PathMeta({ analysis }: { analysis: PathAnalysis }) {
  const parts: string[] = [];

  if (analysis.timeline_months !== null) {
    parts.push(`${analysis.timeline_months} months to capability`);
  }
  if (analysis.estimated_cost_usd !== null) {
    parts.push(
      `$${analysis.estimated_cost_usd.toLocaleString("en-US")} estimated`,
    );
  }
  if (analysis.candidates.length > 0) {
    parts.push(
      `${analysis.candidates.length} ${
        analysis.candidates.length === 1 ? "candidate" : "candidates"
      }`,
    );
  }

  if (parts.length === 0) return null;

  return (
    <p className="text-sm text-faint">
      {parts.map((part, index) => (
        <span key={part}>
          {index > 0 && <span className="px-2 text-line">/</span>}
          {part}
        </span>
      ))}
    </p>
  );
}
