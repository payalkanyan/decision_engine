"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Check, Copy, X } from "@phosphor-icons/react";
import type { Candidate } from "@/lib/types";
import { MAX_SCORE, formatScore, pathLabel } from "@/lib/score";

interface CandidateModalProps {
  candidate: Candidate | null;
  path: string;
  onClose: () => void;
}

/**
 * Shows only what the scoring engine actually returned.
 *
 * This dialog used to print a "Key Signals" and "Contact Info" block with
 * invented values (a hardcoded "Series A+" funding stage, a "20-200"
 * headcount range, a LinkedIn slug built by lowercasing the company name).
 * None of it came from the API. In a product whose premise is that every
 * score carries provenance, rendering fabricated evidence next to a real
 * score is worse than rendering nothing, so it is gone.
 */
export default function CandidateModal({
  candidate,
  path,
  onClose,
}: CandidateModalProps) {
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!candidate) return;

    const previouslyFocused = document.activeElement as HTMLElement | null;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);
    dialogRef.current?.focus();

    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [candidate, onClose]);

  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(timer);
  }, [copied]);

  if (!candidate) return null;

  const copySummary = async () => {
    const summary = [
      candidate.name,
      `${pathLabel(path)} path, fit score ${formatScore(candidate.score)}/${MAX_SCORE}`,
      candidate.reasoning,
    ].join("\n");

    try {
      await navigator.clipboard.writeText(summary);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-canvas/80 p-4 backdrop-blur-sm sm:items-center"
      onClick={onClose}
      data-testid="candidate-modal"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-xl border border-line bg-surface focus:outline-none"
      >
        <div className="flex items-start justify-between gap-6 border-b border-line p-6">
          <div>
            <h3
              id={titleId}
              className="text-xl font-semibold tracking-tight"
            >
              {candidate.name}
            </h3>
            <p className="mt-1 text-sm text-faint">{pathLabel(path)} path</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="p-1.5 text-faint transition-colors duration-200 hover:bg-raised hover:text-text"
          >
            <X size={18} weight="bold" />
          </button>
        </div>

        <div className="space-y-6 p-6">
          <div>
            <p className="text-sm text-faint">Fit score</p>
            <p className="tnum mt-1 text-4xl tracking-tight text-accent">
              {formatScore(candidate.score)}
              <span className="text-xl text-faint">/{MAX_SCORE}</span>
            </p>
          </div>

          <div>
            <p className="text-sm text-faint">Reasoning</p>
            <p className="mt-2 leading-relaxed text-muted">
              {candidate.reasoning}
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-3 border-t border-line p-4">
          <button
            type="button"
            onClick={copySummary}
            className="inline-flex items-center gap-2 border border-line px-4 py-2 text-sm text-muted transition-colors duration-200 hover:border-chrome hover:text-text active:translate-y-px"
            data-testid="copy-summary"
          >
            {copied ? (
              <Check size={16} weight="bold" />
            ) : (
              <Copy size={16} weight="bold" />
            )}
            {copied ? "Copied" : "Copy summary"}
          </button>
        </div>
      </div>
    </div>
  );
}
