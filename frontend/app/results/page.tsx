"use client";

import { Suspense, useCallback, useEffect, useState, ViewTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import PixelTerminalDock from "@/components/PixelTerminalDock";
import SiteFooter from "@/components/SiteFooter";
import ResultsView from "@/components/ResultsView";
import LoadingState from "@/components/LoadingState";
import ErrorState from "@/components/ErrorState";
import { analyzeStrategy } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

const NAV_TRANSITIONS = {
  "nav-forward": "nav-forward",
  "nav-back": "nav-back",
  default: "none",
} as const;

type RequestState =
  | { status: "loading" }
  | { status: "ready"; data: AnalyzeResponse }
  | { status: "error"; message: string };

/**
 * fetch rejects with a bare TypeError ("Failed to fetch") for DNS, CORS and
 * connection failures, which tells the reader nothing they can act on.
 * Anything else is a message the API itself chose, so it passes through.
 */
function describeFailure(error: unknown): string {
  if (error instanceof TypeError) {
    return "Could not reach the scoring service. Check your connection, then try again.";
  }
  return error instanceof Error ? error.message : "Failed to analyze strategy";
}

function ResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const company = searchParams.get("company");
  const capability = searchParams.get("capability");

  const [state, setState] = useState<RequestState>({ status: "loading" });

  /**
   * Nothing is set synchronously here: the first statement is the request
   * itself, so mounting does not trigger a cascading render, and an aborted
   * run resolves without touching state at all. That last part matters when
   * the reader changes the query mid-flight, where the previous version could
   * land a stale response over a newer one.
   */
  const runAnalysis = useCallback(
    async (signal?: AbortSignal) => {
      if (!company || !capability) return;

      try {
        const data = await analyzeStrategy(company, capability, signal);
        if (signal?.aborted) return;
        setState({ status: "ready", data });
      } catch (e) {
        if (signal?.aborted) return;
        setState({ status: "error", message: describeFailure(e) });
      }
    },
    [company, capability],
  );

  useEffect(() => {
    if (!company || !capability) {
      router.replace("/");
      return;
    }

    const controller = new AbortController();
    // The rule cannot see across the await inside runAnalysis. Every setState
    // in there is behind the network round trip, so this does not cascade a
    // render on mount. Moving the fetch to a Server Component would remove
    // the effect outright, but that changes which network reaches the API.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void runAnalysis(controller.signal);
    return () => controller.abort();
  }, [company, capability, runAnalysis, router]);

  const handleRetry = useCallback(() => {
    setState({ status: "loading" });
    void runAnalysis();
  }, [runAnalysis]);

  if (!company || !capability) return null;

  if (state.status === "loading") {
    return <LoadingState capability={capability} />;
  }

  if (state.status === "error") {
    return <ErrorState message={state.message} onRetry={handleRetry} />;
  }

  return <ResultsView data={state.data} />;
}

export default function ResultsPage() {
  return (
    <>
      <PixelTerminalDock />

      <ViewTransition
        enter={NAV_TRANSITIONS}
        exit={NAV_TRANSITIONS}
        default="none"
      >
        <main className="flex-1">
          <div className="mx-auto max-w-7xl px-6 py-16 lg:px-10 lg:py-24">
            <Suspense fallback={<LoadingState />}>
              <ResultsContent />
            </Suspense>
          </div>
        </main>
      </ViewTransition>

      <SiteFooter />
    </>
  );
}
