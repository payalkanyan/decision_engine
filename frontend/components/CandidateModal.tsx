import { useEffect } from "react";
import type { Candidate } from "@/lib/types";

interface CandidateModalProps {
  candidate: Candidate | null;
  onClose: () => void;
  path: string;
}

export default function CandidateModal({
  candidate,
  onClose,
  path,
}: CandidateModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (candidate) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleEscape);
    }
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleEscape);
    };
  }, [candidate, onClose]);

  if (!candidate) return null;

  const copyContactList = async () => {
    const text = `${candidate.name}\nScore: ${candidate.score}/10\n${candidate.reasoning}`;
    await navigator.clipboard.writeText(text);
  };

  const shareAnalysis = async () => {
    if (navigator.share) {
      await navigator.share({
        title: `Strategy Analysis: ${candidate.name}`,
        text: `${candidate.name} — Fit Score: ${candidate.score}/10\n${candidate.reasoning}`,
      });
    } else {
      await navigator.clipboard.writeText(candidate.name);
    }
  };

  const pathColor =
    path === "partner"
      ? "text-emerald-400"
      : path === "acquire"
        ? "text-amber-400"
        : "text-crustdata-blue";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
      data-testid="candidate-modal"
    >
      <div
        className="bg-crustdata-dark border border-gray-700 rounded-xl shadow-2xl max-w-2xl w-full mx-4 transform transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-gray-700/50">
          <h3 className="text-xl font-bold text-crustdata-light">
            {candidate.name}
          </h3>
          <span
            className={`text-sm font-medium ${pathColor} bg-crustdata-dark/30 px-3 py-1 rounded-full`}
          >
            {path.charAt(0).toUpperCase() + path.slice(1)} Path
          </span>
        </div>

        <div className="p-6 space-y-5">
          <div>
            <span className="text-sm font-medium text-crustdata-light/60">
              Fit Score
            </span>
            <p className="text-3xl font-bold text-crustdata-blue mt-1">
              {candidate.score.toFixed(1)}/10
            </p>
          </div>

          <div>
            <span className="text-sm font-medium text-crustdata-light/60">
              Reasoning
            </span>
            <p className="text-crustdata-light/80 mt-1 leading-relaxed">
              {candidate.reasoning}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="bg-crustdata-dark/30 rounded-lg p-4 border border-gray-700/30">
              <span className="text-xs font-medium text-crustdata-light/60 uppercase">
                Key Signals
              </span>
              <ul className="mt-2 space-y-1 text-sm text-crustdata-light/70">
                <li>Tech stack aligned with {candidate.name.split(" ")[0]}</li>
                <li>Funding stage: Series A+</li>
                <li>Headcount: 20-200 range</li>
              </ul>
            </div>
            <div className="bg-crustdata-dark/30 rounded-lg p-4 border border-gray-700/30">
              <span className="text-xs font-medium text-crustdata-light/60 uppercase">
                Contact Info
              </span>
              <ul className="mt-2 space-y-1 text-sm text-crustdata-light/70">
                <li>Partnerships team</li>
                <li>Technical leadership</li>
                <li>LinkedIn: linkedin.com/company/{candidate.name.toLowerCase().replace(/\s/g, "-")}</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 p-4 border-t border-gray-700/50 bg-crustdata-dark/20 rounded-b-xl">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-crustdata-light/70 hover:text-crustdata-light hover:bg-crustdata-dark/30 rounded-lg transition-colors border border-gray-700/30"
          >
            Close
          </button>
          <button
            onClick={copyContactList}
            className="px-4 py-2 text-sm text-crustdata-light hover:text-crustdata-blue hover:bg-crustdata-dark/30 rounded-lg transition-colors border border-crustdata-blue/30"
            data-testid="copy-contact"
          >
            Copy Contact List
          </button>
          <button
            onClick={shareAnalysis}
            className="px-4 py-2 text-sm font-medium text-white hover:bg-crustdata-blue/90 bg-crustdata-blue rounded-lg transition-colors"
            data-testid="share-analysis"
          >
            Share Analysis
          </button>
        </div>
      </div>
    </div>
  );
}
