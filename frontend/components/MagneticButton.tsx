"use client";

import { useEffect, useRef, type ReactNode } from "react";

interface MagneticButtonProps {
  children: ReactNode;
  className?: string;
  /** How far the element leans toward the pointer, as a fraction of offset. */
  strength?: number;
}

/**
 * Pulls its child toward the pointer and springs back on leave.
 *
 * Motion justification: feedback. The primary action acknowledges the pointer
 * before the click lands.
 *
 * The transform is written straight to the node inside a rAF loop that lerps
 * toward the target, so there is no React state and no re-render on
 * pointermove. The loop only runs while the element is being tracked or is
 * still settling, so an idle button costs nothing.
 *
 * Skipped entirely without a hover-capable pointer or under reduced motion,
 * which leaves touch devices and reduced-motion readers a plain static button.
 */
export default function MagneticButton({
  children,
  className,
  strength = 0.3,
}: MagneticButtonProps) {
  const scope = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scope.current;
    if (!el) return;

    const canAnimate = window.matchMedia(
      "(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)",
    ).matches;
    if (!canAnimate) return;

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let frame = 0;

    const loop = () => {
      currentX += (targetX - currentX) * 0.14;
      currentY += (targetY - currentY) * 0.14;

      const settled =
        Math.abs(targetX - currentX) < 0.1 && Math.abs(targetY - currentY) < 0.1;
      if (settled) {
        currentX = targetX;
        currentY = targetY;
      }

      el.style.transform = `translate3d(${currentX.toFixed(2)}px, ${currentY.toFixed(2)}px, 0)`;
      frame = settled && targetX === 0 && targetY === 0 ? 0 : requestAnimationFrame(loop);
    };

    const start = () => {
      if (!frame) frame = requestAnimationFrame(loop);
    };

    const onMove = (event: PointerEvent) => {
      const box = el.getBoundingClientRect();
      targetX = (event.clientX - (box.left + box.width / 2)) * strength;
      targetY = (event.clientY - (box.top + box.height / 2)) * strength * 1.4;
      start();
    };

    const onLeave = () => {
      targetX = 0;
      targetY = 0;
      start();
    };

    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerleave", onLeave);

    return () => {
      if (frame) cancelAnimationFrame(frame);
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerleave", onLeave);
      el.style.transform = "";
    };
  }, [strength]);

  // The negative margin widens the magnetic field past the button's own box
  // without changing where it sits in the layout.
  return (
    <div ref={scope} className={`-m-4 w-fit p-4 ${className ?? ""}`}>
      {children}
    </div>
  );
}
