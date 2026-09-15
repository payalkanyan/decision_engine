export const CRUSTDATA_DARK = "#1a1f2e";
export const CRUSTDATA_BLUE = "#0066ff";
export const CRUSTDATA_ACCENT = "#00d4ff";
export const CRUSTDATA_LIGHT = "#e8e8e8";
export const CRUSTDATA_WHITE = "#ffffff";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://decision-engine-209363122989.us-central1.run.app";

export const EXAMPLE_COMPANIES = ["Google", "Stripe", "Meta", "OpenAI"];
export const EXAMPLE_CAPABILITIES = [
  "AI voice",
  "Real-time analytics",
  "Blockchain",
  "Computer vision",
];

export const PATH_CONFIG: Record<string, { label: string; color: string }> = {
  build: { label: "Build", color: "bg-crustdata-blue" },
  partner: { label: "Partner", color: "bg-emerald-500" },
  acquire: { label: "Acquire", color: "bg-amber-500" },
};
