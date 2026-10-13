"use client";

import Link from "next/link";
import { ArrowLeft } from "@phosphor-icons/react";
import type { AnalyzeResponse } from "@/lib/types";
import { getRecommendation } from "@/lib/score";
import Reveal from "@/components/Reveal";
import RecommendationLead from "@/components/RecommendationLead";
import PathComparison from "@/components/PathComparison";
import CandidateGrid from "@/components/CandidateGrid";

interface ResultsViewProps {
  data: AnalyzeResponse;
}

export default function ResultsView({ data }: ResultsViewProps) {
  const { leader, ranked, isCloseCall } = getRecommendation(data);

  return (
    <div data-testid="results-view">
      <Reveal mode="enter" delay={0.1} className="space-y-12">
        <div
          data-reveal
          className="flex flex-wrap items-center justify-between gap-4"
        >
          <h1 className="text-xl font-medium tracking-tight text-muted">
            <span className="text-text">{data.my_company}</span> entering{" "}
            <span className="text-text">{data.capability}</span>
          </h1>

          <Link
            href="/"
            transitionTypes={["nav-back"]}
            className="group inline-flex items-center gap-2 border border-line px-4 py-2 text-sm text-muted transition-[color,border-color] duration-200 hover:border-chrome hover:text-text"
            data-testid="new-analysis"
          >
            <ArrowLeft
              size={15}
              weight="bold"
              className="transition-transform duration-300 ease-out group-hover:-translate-x-1"
            />
            New analysis
          </Link>
        </div>

        <RecommendationLead leader={leader} isCloseCall={isCloseCall} />
      </Reveal>

      <Reveal mode="batch">
        <PathComparison ranked={ranked} leader={leader} />
        <CandidateGrid paths={ranked} />
      </Reveal>
    </div>
  );
}
