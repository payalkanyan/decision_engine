export const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

/**
 * Read at the moment a timeline would start rather than mirrored into state,
 * so a reader who flips the setting mid-session gets the new behaviour on the
 * next animation without anything re-rendering.
 */
export function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia(REDUCED_MOTION_QUERY).matches
  );
}

/**
 * Fire `onEnter` the first time each element is in view, then stop watching it.
 *
 * Elements that enter together arrive in the same callback, which is what lets
 * callers stagger a visible batch without staggering rows the reader cannot
 * see yet. Returns a disconnect function.
 */
export function observeOnce(
  elements: Element[],
  onEnter: (batch: Element[]) => void,
  options: IntersectionObserverInit = { rootMargin: "0px 0px -12% 0px" },
): () => void {
  if (elements.length === 0) return () => {};

  // Without IntersectionObserver nothing would ever reveal, so show it all.
  if (typeof IntersectionObserver === "undefined") {
    onEnter(elements);
    return () => {};
  }

  const observer = new IntersectionObserver((entries) => {
    const entered = entries
      .filter((entry) => entry.isIntersecting)
      .map((entry) => entry.target);
    if (entered.length === 0) return;
    entered.forEach((element) => observer.unobserve(element));
    onEnter(entered);
  }, options);

  elements.forEach((element) => observer.observe(element));
  return () => observer.disconnect();
}

/**
 * requestAnimationFrame tween over a scalar. Returns a cancel function.
 * Values are handed to `onFrame`; nothing here touches React state.
 */
export function tween(
  from: number,
  to: number,
  duration: number,
  onFrame: (value: number) => void,
): () => void {
  let frame = 0;
  const start = performance.now();
  // Matches the ease the CSS transitions use, so JS-driven and CSS-driven
  // motion on the same screen decelerate together.
  const easeOutQuint = (t: number) => 1 - Math.pow(1 - t, 5);

  const step = (now: number) => {
    const progress = Math.min(1, (now - start) / duration);
    onFrame(from + (to - from) * easeOutQuint(progress));
    frame = progress < 1 ? requestAnimationFrame(step) : 0;
  };

  frame = requestAnimationFrame(step);
  return () => {
    if (frame) cancelAnimationFrame(frame);
  };
}
