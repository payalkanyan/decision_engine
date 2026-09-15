"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ResultsCards from "@/components/ResultsCards";
import LoadingState from "@/components/LoadingState";
import ErrorState from "@/components/ErrorState";
import { analyzeStrategy } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

function ResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const company = searchParams.get("company");
  const capability = searchParams.get("capability");

  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = async () => {
    if (!company || !capability) return;

    setIsLoading(true);
    setError(null);
    try {
      const result = await analyzeStrategy(company, capability);
      setData(result);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Failed to analyze strategy",
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!company || !capability) {
      router.replace("/");
      return;
    }
    void fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [company, capability]);

  const handleRetry = () => {
    void fetchData();
  };

  const handleStartOver = () => {
    router.push("/");
  };

  if (!company || !capability) {
    return null;
  }

  return (
    <div className="min-h-screen bg-crustdata-dark text-crustdata-light py-12">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={handleStartOver}
            className="px-4 py-2 text-sm text-crustdata-light/70 hover:text-crustdata-light hover:bg-crustdata-dark/30 rounded-lg border border-crustdata-blue/20 transition-colors"
            data-testid="start-over"
          >
            ← Start Over
          </button>
        </div>

        {isLoading && <LoadingState capability={capability} />}

        {error && (
          <ErrorState message={error} onRetry={handleRetry} />
        )}

        {data && (
          <div className="space-y-8">
            <ResultsCards data={data} />

            <div className="text-center pt-8">
              <button
                onClick={handleStartOver}
                className="px-6 py-3 text-crustdata-light/70 hover:text-crustdata-blue hover:bg-crustdata-dark/30 rounded-lg border border-crustdata-blue/30 transition-colors text-sm"
              >
                Run Another Analysis
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <ResultsContent />
    </Suspense>
  );
}
