import type { PathAnalysis } from "@/lib/types";
import { pathLabel } from "@/lib/score";
import ScoreMeter from "@/components/ScoreMeter";
import MaskedHeadline from "@/components/MaskedHeadline";

interface RecommendationLeadProps {
  leader: PathAnalysis | null;
  isCloseCall: boolean;
}

/**
 * The verdict, given the whole top of the page at display scale.
 *
 * The original layout gave Build, Partner and Acquire identical cards and
 * buried the recommendation in a pill, so the reader had to compare three
 * numbers to find the answer the engine had already picked.
 */
export default function RecommendationLead({
  leader,
  isCloseCall,
}: RecommendationLeadProps) {
  if (!leader) {
    return (
      <section className="border-b border-line pb-20">
        <MaskedHeadline
          as="h2"
          lines={["No path", "could be scored."]}
          className="text-5xl font-semibold tracking-[-0.045em] text-text md:text-7xl md:leading-[0.95]"
        />
        <p className="mt-10 max-w-[62ch] text-lg leading-relaxed text-muted">
          The rubric drops criteria it has no data for rather than scoring them
          as zero, and in this run every criterion was dropped. Check the
          company name and that the Crustdata plan covers these endpoints.
        </p>
      </section>
    );
  }

  return (
    <section className="border-b border-line pb-20">
      <p className="text-xs tracking-[0.2em] text-faint uppercase">
        Recommended path
      </p>

      <div className="mt-8 grid gap-12 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-7">
          <MaskedHeadline
            as="h2"
            lines={[pathLabel(leader.path)]}
            className="text-7xl font-semibold tracking-[-0.05em] text-text md:text-[7.5rem] md:leading-[0.88]"
          />

          <p
            data-reveal
            className="mt-10 max-w-[58ch] text-lg leading-relaxed text-muted"
          >
            {leader.reasoning}
          </p>

          {isCloseCall && (
            <p
              data-reveal
              className="mt-7 max-w-[58ch] border-l-2 border-accent pl-5 text-sm leading-relaxed text-faint"
              data-testid="close-call-note"
            >
              The runner-up is within a point of this score. The rubric does not
              separate them with confidence, so weigh the two paths on the
              evidence below rather than on the gap.
            </p>
          )}
        </div>

        <div data-reveal className="lg:col-span-5 lg:pt-4">
          <ScoreMeter score={leader.score} scored emphasis size="lg" />
          <PathFacts analysis={leader} />
        </div>
      </div>
    </section>
  );
}

export function PathFacts({ analysis }: { analysis: PathAnalysis }) {
  const facts: { label: string; value: string }[] = [];

  if (analysis.timeline_months !== null) {
    facts.push({
      label: "Time to capability",
      value: `${analysis.timeline_months} months`,
    });
  }
  if (analysis.estimated_cost_usd !== null) {
    facts.push({
      label: "Estimated cost",
      value: `$${analysis.estimated_cost_usd.toLocaleString("en-US")}`,
    });
  }
  if (analysis.candidates.length > 0) {
    facts.push({
      label: "Candidates found",
      value: String(analysis.candidates.length),
    });
  }

  if (facts.length === 0) return null;

  return (
    <dl className="mt-12 border-t border-line">
      {facts.map((fact) => (
        <div
          key={fact.label}
          className="flex items-baseline justify-between gap-6 border-b border-line py-4"
        >
          <dt className="text-sm text-faint">{fact.label}</dt>
          <dd className="tnum text-sm text-text">{fact.value}</dd>
        </div>
      ))}
    </dl>
  );
}
