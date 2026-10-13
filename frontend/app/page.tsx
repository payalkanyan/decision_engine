"use client";

import { ViewTransition } from "react";
import { useRouter } from "next/navigation";
import AnalysisForm from "@/components/AnalysisForm";
import MaskedHeadline from "@/components/MaskedHeadline";
import PixelTerminalDock from "@/components/PixelTerminalDock";
import Reveal from "@/components/Reveal";
import SiteFooter from "@/components/SiteFooter";
import { SIGNAL_GROUPS } from "@/lib/constants";

const NAV_TRANSITIONS = {
  "nav-forward": "nav-forward",
  "nav-back": "nav-back",
  default: "none",
} as const;

export default function Home() {
  const router = useRouter();

  const handleSubmit = (company: string, capability: string) => {
    const params = new URLSearchParams({ company, capability });
    router.push(`/results?${params.toString()}`, {
      transitionTypes: ["nav-forward"],
    });
  };

  return (
    <>
      {/* The dock's dithered field is the page's hero visual, so it gets room
          to read as one rather than being squeezed into a 64px bar. */}
      <PixelTerminalDock size="hero" />

      <ViewTransition
        enter={NAV_TRANSITIONS}
        exit={NAV_TRANSITIONS}
        default="none"
      >
        <main className="flex-1">
          {/* Headline and form sit side by side above lg so the primary action
              clears the fold under a field this tall. */}
          <section className="mx-auto max-w-7xl px-6 pt-14 pb-24 lg:px-10 lg:pt-16">
            <div className="grid gap-12 lg:grid-cols-12 lg:gap-16">
              <div className="lg:col-span-6">
                <MaskedHeadline
                  lines={["BUILD, PARTNER", "OR ACQUIRE."]}
                  className="mono text-[1.75rem] leading-[1.1] tracking-[-0.03em] text-text sm:text-4xl lg:text-[3rem]"
                />

                <Reveal mode="enter" delay={0.45} className="mt-7">
                  <p
                    data-reveal
                    className="max-w-[46ch] leading-relaxed text-muted"
                  >
                    Score all three paths to a new capability against live
                    hiring, funding and technographic signals.
                  </p>
                </Reveal>
              </div>

              <Reveal
                mode="enter"
                delay={0.55}
                className="lg:col-span-5 lg:col-start-8"
              >
                <div data-reveal id="analysis-form" className="scroll-mt-28">
                  <AnalysisForm onSubmit={handleSubmit} />
                </div>
              </Reveal>
            </div>
          </section>

          <section id="signals" className="scroll-mt-10 border-t border-line">
            <Reveal className="mx-auto max-w-7xl px-6 py-24 lg:px-10 lg:py-32">
              <div data-reveal className="max-w-[46rem]">
                <h2 className="mono text-2xl tracking-[-0.02em] text-text lg:text-[2.25rem] lg:leading-[1.1]">
                  WHAT THE SCORE IS BUILT FROM
                </h2>
                <p className="mt-6 max-w-[62ch] leading-relaxed text-muted">
                  The rubric reads a deliberately narrow set of signals per
                  path. Nothing is inferred by a language model, and any
                  criterion without data is dropped rather than scored as zero.
                </p>
              </div>

              <dl className="mt-20 border-t border-line">
                {SIGNAL_GROUPS.map((group) => (
                  <div
                    key={group.title}
                    data-reveal
                    className="grid gap-3 border-b border-line py-10 lg:grid-cols-12 lg:gap-10"
                  >
                    <dt className="mono text-lg tracking-[0.02em] text-text lg:col-span-5">
                      {group.title}
                    </dt>
                    <dd className="max-w-[58ch] leading-relaxed text-muted lg:col-span-6 lg:col-start-7">
                      {group.detail}
                    </dd>
                  </div>
                ))}
              </dl>
            </Reveal>
          </section>
        </main>
      </ViewTransition>

      <SiteFooter />
    </>
  );
}
