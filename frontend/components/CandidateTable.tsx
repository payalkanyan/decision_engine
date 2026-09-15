import { useState } from "react";
import type { Candidate } from "@/lib/types";
import CandidateModal from "@/components/CandidateModal";

interface CandidateTableProps {
  candidates: Candidate[];
  path: string;
}

export default function CandidateTable({ candidates, path }: CandidateTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [modalCandidate, setModalCandidate] = useState<Candidate | null>(null);

  if (!candidates || candidates.length === 0) {
    return (
      <div className="text-center py-8 text-crustdata-light/50">
        <p>No candidates available for this path.</p>
      </div>
    );
  }

  const sorted = [...candidates].sort((a, b) => b.score - a.score);
  const headerColor =
    path === "partner"
      ? "text-emerald-400"
      : path === "acquire"
        ? "text-amber-400"
        : "text-crustdata-blue";

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-gray-700/50">
              <th
                className={`text-left py-3 px-4 font-semibold ${headerColor} text-sm uppercase tracking-wider`}
              >
                Company
              </th>
              <th
                className={`text-right py-3 px-4 font-semibold ${headerColor} text-sm uppercase tracking-wider`}
              >
                Fit Score
              </th>
              <th
                className={`text-left py-3 px-4 font-semibold ${headerColor} text-sm uppercase tracking-wider hidden md:table-cell`}
              >
                Summary
              </th>
              <th
                className={`text-center py-3 px-4 font-semibold ${headerColor} text-sm uppercase tracking-wider`}
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((candidate, idx) => (
              <tr
                key={`${candidate.name}-${idx}`}
                className="border-b border-gray-700/30 hover:bg-crustdata-dark/30 transition-colors"
              >
                <td className="py-3 px-4">
                  <button
                    onClick={() => setExpandedId(expandedId === candidate.name ? null : candidate.name)}
                    className="text-left font-medium text-crustdata-light hover:text-crustdata-blue transition-colors flex items-center gap-2"
                  >
                    {candidate.name}
                    <svg
                      className={`w-4 h-4 transition-transform text-crustdata-light/40 ${
                        expandedId === candidate.name ? "rotate-180" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </button>
                </td>
                <td className="py-3 px-4 text-right">
                  <span className="font-bold text-crustdata-blue">
                    {candidate.score.toFixed(1)}/10
                  </span>
                </td>
                <td className="py-3 px-4 text-crustdata-light/70 text-sm hidden md:table-cell">
                  <div
                    className={`overflow-hidden transition-all duration-300 ${
                      expandedId === candidate.name ? "max-h-20" : "max-h-5"
                    }`}
                  >
                    {candidate.reasoning}
                  </div>
                </td>
                <td className="py-3 px-4 text-center">
                  <button
                    onClick={() => setModalCandidate(candidate)}
                    className="px-3 py-1 text-sm text-crustdata-light/80 hover:text-crustdata-blue hover:bg-crustdata-dark/30 rounded border border-crustdata-blue/20 transition-colors"
                    data-testid={`details-${candidate.name}`}
                  >
                    Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <CandidateModal
        candidate={modalCandidate}
        onClose={() => setModalCandidate(null)}
        path={path}
      />
    </>
  );
}
