import type { AnalyzeResponse, AnalysisError } from "@/lib/types";
import { API_URL } from "@/lib/constants";

export async function analyzeStrategy(
  myCompany: string,
  capability: string,
): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_URL}/analyze-strategy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ my_company: myCompany, capability }),
  });

  if (!response.ok) {
    const error: AnalysisError = await response.json();
    throw new Error(error.detail || "Failed to analyze strategy");
  }

  return (await response.json()) as AnalyzeResponse;
}
