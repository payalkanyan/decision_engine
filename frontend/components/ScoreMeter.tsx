"use client";

import { useEffect, useRef } from "react";
import { observeOnce, prefersReducedMotion } from "@/lib/motion";
import { MAX_SCORE, formatScore } from "@/lib/score";
import CountUp from "@/components/CountUp";

interface ScoreMeterProps {
  score: number;
  scored: boolean;
  /** The leading path, which is the only thing on the page allowed the accent. */
  emphasis?: boolean;
  size?: "sm" | "lg";
}

/**
 * A scale reading, not a dashboard progress bar: a hairline track with a drawn
 * fill. Motion justification: feedback. The bar draws to the number the engine
 * computed, so the figure reads as measured rather than typeset.
 *
 * The fill's resting transform is its true width, set inline, so the correct
 * reading is in the DOM before anything animates. The draw scales it up from
 * zero on a CSS transition once it is in view.
 */
export default function ScoreMeter({
  score,
  scored,
  emphasis = false,
  size = "sm",
}: ScoreMeterProps) {
  const fillRef = useRef<HTMLDivElement>(null);
  const ratio = scored ? Math.min(1, Math.max(0, score / MAX_SCORE)) : 0;

  useEffect(() => {
    const fill = fillRef.current;
    if (!fill || prefersReducedMotion()) return;

    fill.style.transform = "scaleX(0)";
    fill.style.transition = "transform 1300ms cubic-bezier(0.16, 1, 0.3, 1)";

    const disconnect = observeOnce([fill], () => {
      fill.style.transform = `scaleX(${ratio})`;
    });

    return () => {
      disconnect();
      fill.style.transition = "";
      fill.style.transform = `scaleX(${ratio})`;
    };
  }, [ratio]);

  const track = size === "lg" ? "h-1" : "h-px";

  return (
    <div className="w-full">
      {scored ? (
        <p
          className={`tnum ${
            size === "lg"
              ? "text-6xl tracking-[-0.055em] md:text-7xl"
              : "text-2xl tracking-[-0.04em]"
          } ${emphasis ? "text-accent" : "text-text"}`}
        >
          <CountUp value={score} />
          <span
            className={`text-faint ${size === "lg" ? "text-3xl" : "text-base"}`}
          >
            /{MAX_SCORE}
          </span>
        </p>
      ) : (
        <p
          className={`text-faint ${size === "lg" ? "text-3xl" : "text-base"}`}
          data-testid="score-no-data"
        >
          Not scored
        </p>
      )}

      <div
        role="meter"
        aria-valuenow={scored ? score : undefined}
        aria-valuemin={0}
        aria-valuemax={MAX_SCORE}
        aria-valuetext={
          scored ? `${formatScore(score)} of ${MAX_SCORE}` : "No data"
        }
        aria-label="Path score"
        className={`mt-4 w-full overflow-hidden ${track} ${
          scored
            ? "bg-line"
            : "bg-[repeating-linear-gradient(to_right,var(--color-line)_0_6px,transparent_6px_12px)]"
        }`}
      >
        {scored && (
          <div
            ref={fillRef}
            style={{ transform: `scaleX(${ratio})` }}
            className={`${track} origin-left ${
              emphasis ? "bg-accent" : "bg-muted"
            }`}
          />
        )}
      </div>
    </div>
  );
}
