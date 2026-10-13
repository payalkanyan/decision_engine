"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  createTopDockController,
  type TopDockOptions,
} from "@/components/vendor/pixel-terminal/topDockController";

/**
 * ThreeUI "Pixel Terminal" (AnimatedTopDock, variant retro), adapted into a
 * working navigation bar.
 *
 * The published component renders a fixed demo: brand "SABLE//OS", five menu
 * items (SYSTEM / METHOD / WORK / ACCESS / NOTES) wired to local state, and a
 * "RUN" button that does nothing. It exposes no items or children prop, so the
 * markup here is ours while the dithered WebGL field and the spring layout
 * controller are the upstream ones, vendored unmodified under ./vendor.
 *
 * What is kept: the fitted strip (cells own the whole track and trade width
 * with each other under pointer proximity), the 8x8 ordered dither over the
 * eight-stop dusk ramp, the scanline overlay and the vignette.
 *
 * What changed: items are real routes with the current one marked, the brand
 * links home, the trailing cell credits the data provider, and the fake
 * telemetry readout ("MEM 640K / DITHER 8x8 / PAL 8") is gone because it is
 * decoration pretending to be instrumentation.
 */

const FIELD_OPTIONS = {
  pixelSize: 4,
  noise: 1,
  levels: 7,
  speed: 1,
} as const;

const DOCK_OPTIONS: TopDockOptions = {
  proximity: 132,
  spring: 0.19,
  damping: 0.7,
  widthGrowth: 54,
  heightGrowth: 16,
  drop: 3.5,
  axis: "x",
  distribute: true,
};

interface DockItem {
  href: string;
  label: string;
  icon: ReactNode;
}

/**
 * Every entry goes somewhere real. The upstream demo ships five cells; this
 * app has two routes and one in-page section, and padding the strip with
 * invented destinations would be the same defect as leaving "SABLE//OS" on it.
 */
const ITEMS: readonly DockItem[] = [
  {
    href: "/",
    label: "ANALYZE",
    icon: (
      <>
        <rect x="0" y="0" width="3" height="3" />
        <rect x="4" y="4" width="3" height="3" />
      </>
    ),
  },
  {
    href: "/#signals",
    label: "SIGNALS",
    icon: (
      <>
        <rect x="0" y="4" width="2" height="3" />
        <rect x="2.5" y="2" width="2" height="5" />
        <rect x="5" y="0" width="2" height="7" />
      </>
    ),
  },
];

function useDockController(getOptions: () => TopDockOptions) {
  const rootRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return undefined;
    return createTopDockController(root, getOptions);
    // The getter is a stable ref reader, so the controller is built once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return rootRef;
}

/**
 * Host lifecycle for the WebGL field: measure from the shell, pause off-screen
 * and on a hidden tab, hand the renderer a css-pixel box. The module resolves
 * in its own effect so the effect owning the GL context can create and tear it
 * down synchronously; an async create survives its own cleanup and leaves two
 * renderers fighting over one canvas.
 */
function usePixelField() {
  const hostRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [factory, setFactory] = useState<{
    create: (
      canvas: HTMLCanvasElement,
      getOptions: () => typeof FIELD_OPTIONS,
    ) => { resize: (w: number, h: number) => void; render: (now: number) => void; dispose: () => void };
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    void import("@/components/vendor/pixel-terminal/retroPixelField").then(
      (m) => {
        if (!cancelled) setFactory({ create: m.createRetroPixelField });
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const host = hostRef.current;
    const canvas = canvasRef.current;
    if (!factory || !host || !canvas) return undefined;

    const field = factory.create(canvas, () => FIELD_OPTIONS);
    let frame = 0;
    let visible = true;
    let bounds = host.getBoundingClientRect();

    const resize = () => {
      bounds = host.getBoundingClientRect();
      field.resize(bounds.width, bounds.height);
    };
    const tick = (now: number) => {
      field.resize(bounds.width, bounds.height);
      field.render(now);
      frame = visible && !document.hidden ? requestAnimationFrame(tick) : 0;
    };

    const resizeObserver = new ResizeObserver(resize);
    const intersection = new IntersectionObserver(([entry]) => {
      visible = entry?.isIntersecting ?? true;
      if (visible && !frame) frame = requestAnimationFrame(tick);
      if (!visible && frame) {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    });

    resizeObserver.observe(host);
    intersection.observe(host);
    resize();
    frame = requestAnimationFrame(tick);

    return () => {
      if (frame) cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      intersection.disconnect();
      field.dispose();
    };
  }, [factory]);

  return { hostRef, canvasRef };
}

interface PixelTerminalDockProps {
  /** "hero" gives the field room to read as the page's main visual. */
  size?: "hero" | "band";
}

export default function PixelTerminalDock({
  size = "band",
}: PixelTerminalDockProps) {
  const pathname = usePathname();
  const { hostRef, canvasRef } = usePixelField();
  const rootRef = useDockController(() => DOCK_OPTIONS);

  return (
    <div
      ref={hostRef}
      style={{ viewTransitionName: "site-header" }}
      className={`ptd ${size === "hero" ? "ptd--hero" : "ptd--band"}`}
    >
      <canvas ref={canvasRef} className="ptd__field" aria-hidden="true" />
      <div className="ptd__vignette" aria-hidden="true" />

      <header className="ptd__bar">
        <Link href="/" transitionTypes={["nav-back"]} className="ptd__brand">
          <span className="ptd__badge" aria-hidden="true">
            <svg viewBox="0 0 7 7">
              <rect x="0" y="2" width="7" height="3" />
              <rect x="2" y="0" width="3" height="7" />
            </svg>
          </span>
          DECISION//ENGINE
        </Link>

        <nav
          ref={rootRef}
          className="ptd__dock"
          aria-label="Primary"
          data-dock-state="idle"
          data-dock-max="0.00"
        >
          {ITEMS.map((item) => {
            // A hash link points at a section, never at the current page, so
            // only a hashless exact match is marked. Without this every
            // "/#..." item also matches on "/" and the whole strip lights up.
            const current = !item.href.includes("#") && pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                data-dock-item
                className="ptd__item"
                aria-current={current ? "page" : undefined}
                // Below 600px the stylesheet hides the label to fit the strip,
                // which also drops it from the accessibility tree and leaves a
                // link named only by a decorative icon.
                aria-label={item.label}
              >
                <span className="ptd__icon" aria-hidden="true">
                  <svg viewBox="0 0 7 7">{item.icon}</svg>
                </span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Outbound credit to the data provider. target=_blank needs the
            noopener/noreferrer pair, and the destination is named in the
            label so the arrow is decoration rather than the only cue. */}
        <a
          href="https://crustdata.com"
          target="_blank"
          rel="noopener noreferrer"
          className="ptd__cta"
          aria-label="Crustdata (opens in a new tab)"
        >
          CRUSTDATA
          <span aria-hidden="true">&#8599;</span>
        </a>
      </header>
    </div>
  );
}
