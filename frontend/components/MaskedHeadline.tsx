"use client";

interface MaskedHeadlineProps {
  /** One entry per rendered line. Line breaks are a composition choice here,
   *  not something left to the browser. */
  lines: string[];
  className?: string;
  as?: "h1" | "h2";
}

/**
 * Headline that wipes up line by line out of its own clipping window.
 *
 * Motion justification: hierarchy. This is the first thing on the page and the
 * wipe sets reading order before anything else competes for attention.
 *
 * Pure CSS: the keyframes and the reduced-motion override live in globals.css,
 * so this runs with no script and nothing to clean up. The per-line delay is
 * passed as a custom property rather than inline animation shorthand so the
 * stylesheet keeps ownership of the timing.
 */
export default function MaskedHeadline({
  lines,
  className,
  as: Tag = "h1",
}: MaskedHeadlineProps) {
  return (
    <Tag className={className}>
      {lines.map((line, index) => (
        <span key={line} className="mask-window">
          <span
            data-mask-line
            className="block"
            style={{ "--line-index": index } as React.CSSProperties}
          >
            {line}
          </span>
        </span>
      ))}
    </Tag>
  );
}
