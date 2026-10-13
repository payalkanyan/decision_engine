"use client";

import { useEffect, useRef } from "react";
import { observeOnce, prefersReducedMotion, tween } from "@/lib/motion";

interface CountUpProps {
  value: number;
  decimals?: number;
  className?: string;
}

/**
 * Counts a number up to its value when it scrolls into view.
 *
 * Motion justification: feedback. The score was computed, so it arrives by
 * being counted rather than by being typeset.
 *
 * The final value is what renders on the server and what sits in the DOM
 * before any animation runs, so the correct number is present without JS and
 * the element never animates away from truth.
 */
export default function CountUp({
  value,
  decimals = 1,
  className,
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const final = value.toFixed(decimals);
    if (prefersReducedMotion()) {
      el.textContent = final;
      return;
    }

    let cancelTween: (() => void) | undefined;

    // Zeroed at the moment the tween starts rather than on mount, so a score
    // that has not been scrolled to yet still holds its real value, and one
    // already in view does not flash the answer before counting to it.
    const disconnect = observeOnce([el], () => {
      el.textContent = (0).toFixed(decimals);
      cancelTween = tween(0, value, 1300, (current) => {
        el.textContent = current.toFixed(decimals);
      });
    });

    return () => {
      disconnect();
      cancelTween?.();
      el.textContent = final;
    };
  }, [value, decimals]);

  return (
    <span ref={ref} className={className}>
      {value.toFixed(decimals)}
    </span>
  );
}
