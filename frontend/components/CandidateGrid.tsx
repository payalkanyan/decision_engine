"use client";

import { useState } from "react";
import { ArrowUpRight } from "@phosphor-icons/react";
import type { Candidate, PathAnalysis } from "@/lib/types";
import { MAX_SCORE, formatScore, pathLabel } from "@/lib/score";
import CandidateModal from "@/components/CandidateModal";

interface CandidateGridProps {
  paths: PathAnalysis[];
}

interface Selection {
  candidate: Candidate;
  path: string;
}

/**
 * Candidates at full page width, grouped by path.
 *
 * They previously lived in a four-column table squeezed inside a one-third
 * card, which overflowed horizontally on every viewport and clipped the
 * summary column. Width is the fix; a table was never the problem.
 */
export default function CandidateGrid({ paths }: CandidateGridProps) {
  const [selected, setSelected] = useState<Selection | null>(null);
  const withCandidates = paths.filter((path) => path.candidates.length > 0);

  if (withCandidates.length === 0) return null;

  return (
    <>
      <section className="space-y-24 pt-28">
        {withCandidates.map((path) => {
          const sorted = [...path.candidates].sort((a, b) => b.score - a.score);

          return (
            <div key={path.path} data-testid={`candidates-${path.path}`}>
              <h3
                data-reveal
                className="text-3xl font-semibold tracking-[-0.03em] lg:text-[2.75rem]"
              >
                {pathLabel(path.path)} candidates
              </h3>

              <ul className="mt-14 grid gap-x-16 gap-y-12 md:grid-cols-2">
                {sorted.map((candidate) => (
                  <li
                    key={candidate.name}
                    data-reveal
                    className="group border-t border-line pt-6"
                  >
                    <div className="flex items-baseline justify-between gap-4">
                      <h4 className="text-xl font-medium tracking-[-0.02em]">
                        {candidate.name}
                      </h4>
                      <p className="tnum shrink-0 text-xl tracking-[-0.03em] text-text">
                        {formatScore(candidate.score)}
                        <span className="text-sm text-faint">/{MAX_SCORE}</span>
                      </p>
                    </div>

                    <p className="mt-4 line-clamp-3 leading-relaxed text-muted">
                      {candidate.reasoning}
                    </p>

                    <button
                      type="button"
                      onClick={() => setSelected({ candidate, path: path.path })}
                      className="mt-5 inline-flex items-center gap-1.5 text-sm text-faint transition-colors duration-200 hover:text-accent"
                      data-testid={`details-${candidate.name}`}
                    >
                      Full reasoning
                      <ArrowUpRight
                        size={15}
                        weight="bold"
                        className="transition-transform duration-300 ease-out group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                      />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </section>

      <CandidateModal
        candidate={selected?.candidate ?? null}
        path={selected?.path ?? ""}
        onClose={() => setSelected(null)}
      />
    </>
  );
}
