export interface Candidate {
  name: string;
  score: number;
  reasoning: string;
}

export interface PathAnalysis {
  path: string;
  score: number;
  reasoning: string;
  timeline_months: number | null;
  estimated_cost_usd: number | null;
  candidates: Candidate[];
}

export interface AnalyzeResponse {
  my_company: string;
  capability: string;
  build_analysis: PathAnalysis;
  partner_analysis: PathAnalysis;
  acquire_analysis: PathAnalysis;
}

export interface AnalysisError {
  detail: string;
}

export type AnalysisResult = AnalyzeResponse | AnalysisError;
