import { NextRequest, NextResponse } from "next/server";
import type { AnalyzeResponse } from "@/lib/types";

export async function POST(request: NextRequest) {
  const { my_company, capability } = await request.json();

  if (!my_company || !capability) {
    return NextResponse.json(
      { detail: "my_company and capability are required" },
      { status: 400 },
    );
  }

  // Simulate API latency
  await new Promise((r) => setTimeout(r, 800));

  const data: AnalyzeResponse = {
    my_company,
    capability,
    build_analysis: {
      path: "build",
      score: 8.65,
      reasoning:
        "Your company has strong existing ML/AI hiring velocity (12+ relevant postings in the last 12 months) and a tech stack that overlaps with " +
        capability +
        ". The estimated time to capability is 5 months with an estimated cost of ~$1.85M.",
      timeline_months: 5,
      estimated_cost_usd: 1850000,
      candidates: [],
    },
    partner_analysis: {
      path: "partner",
      score: 7.8,
      reasoning:
        "Several strong ecosystem partners with complementary customer bases and proven voice AI capabilities are available for strategic partnerships.",
      timeline_months: null,
      estimated_cost_usd: null,
      candidates: [
        {
          name: "OpenAI",
          score: 9.5,
          reasoning:
            "Best-in-class voice AI API platform with strong market position and existing enterprise adoption.",
        },
        {
          name: "AssemblyAI",
          score: 8.7,
          reasoning:
            "Specialized voice AI API with high accuracy transcription and strong developer experience.",
        },
        {
          name: "Deepgram",
          score: 8.2,
          reasoning:
            "Real-time voice AI with enterprise-grade infrastructure and competitive pricing.",
        },
      ],
    },
    acquire_analysis: {
      path: "acquire",
      score: 7.1,
      reasoning:
        "Multiple acquirable targets with proven voice AI products, strong founding teams, and reasonable valuations.",
      timeline_months: null,
      estimated_cost_usd: null,
      candidates: [
        {
          name: "Voiceflow",
          score: 8.0,
          reasoning:
            "45-person team with strong product-market fit in voice agents, Series B funded, ideal acquirable size.",
        },
        {
          name: "Descript",
          score: 7.5,
          reasoning:
            "120-person team with popular consumer voice product, Series C funded, moderate integration complexity.",
        },
        {
          name: "Sonantic",
          score: 6.8,
          reasoning:
            "Voice synthesis specialist with strong AI talent, acquired-sized team, strategic fit.",
        },
      ],
    },
  };

  return NextResponse.json(data);
}
