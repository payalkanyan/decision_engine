"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { observeOnce, prefersReducedMotion } from "@/lib/motion";

interface RevealProps {
  children: ReactNode;
  /**
   * How the group's `[data-reveal]` descendants arrive:
   *   enter  - on mount, for content above the fold
   *   scroll - together, when the first of them comes into view
   *   batch  - per element, staggered within each visible batch. Use this for
   *            sections taller than the viewport, where revealing everything
   *            at once would animate rows the reader cannot see yet.
   * Sequence comes from document order, not per-element props.
   */
  mode?: "enter" | "scroll" | "batch";
  delay?: number;
  stagger?: number;
  className?: string;
}

const DURATION = 900;
const EASE = "cubic-bezier(0.16, 1, 0.3, 1)";

/**
 * Scoped entrance for a group of elements, on IntersectionObserver and CSS
 * transitions.
 *
 * Motion justification: order of arrival carries the hierarchy. On the entry
 * page the headline lands before the form; on the results page the verdict
 * lands before the alternatives it beat.
 */
export default function Reveal({
  children,
  mode = "scroll",
  delay = 0,
  stagger = 0.09,
  className,
}: RevealProps) {
  const scope = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = scope.current;
    if (!root) return;

    const targets = Array.from(
      root.querySelectorAll<HTMLElement>("[data-reveal]"),
    );
    if (targets.length === 0) return;

    const show = (element: HTMLElement, index: number) => {
      element.style.transitionDelay = `${delay * 1000 + index * stagger * 1000}ms`;
      element.style.opacity = "1";
      element.style.transform = "none";
    };

    if (prefersReducedMotion()) {
      targets.forEach((element) => {
        element.style.opacity = "1";
        element.style.transform = "none";
      });
      return;
    }

    targets.forEach((element) => {
      element.style.transform = "translateY(26px)";
      element.style.transition = `opacity ${DURATION}ms ${EASE}, transform ${DURATION}ms ${EASE}`;
      element.style.willChange = "opacity, transform";
    });

    if (mode === "enter") {
      // Two frames: one for the initial state to be committed, one for the
      // transition to have something to animate from.
      const frame = requestAnimationFrame(() =>
        requestAnimationFrame(() => targets.forEach(show)),
      );
      return () => cancelAnimationFrame(frame);
    }

    if (mode === "batch") {
      return observeOnce(targets, (batch) =>
        batch.forEach((element, index) => show(element as HTMLElement, index)),
      );
    }

    // "scroll": the whole group arrives together once any of it is in view.
    return observeOnce([targets[0]], () => targets.forEach(show));
  }, [mode, delay, stagger]);

  return (
    <div ref={scope} className={className}>
      {children}
    </div>
  );
}
