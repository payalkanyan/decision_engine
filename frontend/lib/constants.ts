export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://decision-engine-209363122989.us-central1.run.app";

export const EXAMPLE_COMPANIES = ["Stripe", "Retool", "Ramp", "Vercel"];

export const EXAMPLE_CAPABILITIES = [
  "AI voice",
  "Real-time analytics",
  "Fraud detection",
  "Computer vision",
];

/**
 * The signal families the scoring engine actually reads, per AGENTS.md
 * section 3. Shown on the entry page so the answer arrives with its
 * sourcing already on the table.
 */
export const SIGNAL_GROUPS = [
  {
    title: "Internal readiness",
    detail:
      "Technographics, headcount by function over time, and open roles that show where engineering effort is already going.",
  },
  {
    title: "Market structure",
    detail:
      "The filterable company graph, funding milestones and investor portfolios that say who already owns the capability.",
  },
  {
    title: "Target viability",
    detail:
      "Decision-maker coverage, founder and team activity, and web traffic trend for every candidate the engine surfaces.",
  },
] as const;
