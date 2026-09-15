"use client";

import { useRouter } from "next/navigation";
import AnalysisForm from "@/components/AnalysisForm";

export default function Home() {
  const router = useRouter();

  const handleSubmit = (company: string, capability: string) => {
    const params = new URLSearchParams({
      company,
      capability,
    });
    router.push(`/results?${params.toString()}`);
  };

  return (
    <div className="min-h-screen bg-crustdata-dark text-crustdata-light flex flex-col">
      <div className="flex-1 container mx-auto px-6 py-16 md:py-24 max-w-4xl">
        <div className="text-center mb-16 space-y-6">
          <h1 className="text-4xl md:text-5xl font-bold text-crustdata-light">
            Build vs Partner vs{" "}
            <span className="text-crustdata-blue">Acquire</span>{" "}
            Intelligence
          </h1>
          <p className="text-lg text-crustdata-light/70 max-w-2xl mx-auto leading-relaxed">
            Analyze your company's best path to entering a new market
            capability — backed by real technographic and hiring data.
          </p>
        </div>

        <AnalysisForm onSubmit={handleSubmit} />
      </div>

      <footer className="py-6 text-center text-crustdata-light/40 text-sm">
        <p>Powered by Crustdata intelligence</p>
      </footer>
    </div>
  );
}
