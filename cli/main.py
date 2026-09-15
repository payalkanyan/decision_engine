import argparse

from data.caching_client import CachingClient
from llm.synthesize import (
    synthesize_acquire_reasoning,
    synthesize_build_reasoning,
    synthesize_partner_reasoning,
)
from scoring.engine import analyze_strategy, get_candidates, load_rubric_yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="Build vs Partner vs Acquire Decision Engine")
    parser.add_argument("--my-company", required=True, help="Your company name")
    parser.add_argument(
        "--capability", required=True, help="Capability to analyze, e.g. 'AI voice'"
    )
    args = parser.parse_args()

    try:
        # 1. Fetch my company data
        print(f"\n📊 Analyzing strategy for {args.my_company}")
        print(f"Capability: {args.capability}")
        print("\nFetching company data...")
        caching_client = CachingClient()
        my_company_data, provenance = caching_client.get_company_enrichment(args.my_company)
        print(f"Data fetched (cache_hit={provenance.cache_hit})")

        # 1b. Fetch own company's jobs + headcount for build path scoring (optional)
        try:
            my_company_jobs, _ = caching_client.get_jobs(args.my_company)
        except Exception:
            my_company_jobs = None
        try:
            my_company_headcount, _ = caching_client.get_headcount_timeseries(args.my_company)
        except Exception:
            my_company_headcount = None

        # 2. Get candidates for each path (optional — degrade gracefully)
        print("\nSearching for candidates...")
        try:
            build_candidates = get_candidates(caching_client, args.capability, "build")
        except Exception:
            build_candidates = []
        try:
            partner_candidates = get_candidates(caching_client, args.capability, "partner")
        except Exception:
            partner_candidates = []
        try:
            acquire_candidates = get_candidates(caching_client, args.capability, "acquire")
        except Exception:
            acquire_candidates = []
        print(
            f"Found {len(build_candidates)} build, "
            f"{len(partner_candidates)} partner, "
            f"{len(acquire_candidates)} acquire candidates"
        )

        # 3. Run strategy analysis
        print("\nScoring all 3 paths...")
        rubric = load_rubric_yaml("rubric.yaml")
        analysis = analyze_strategy(
            my_company=args.my_company,
            capability=args.capability,
            my_company_enrichment=my_company_data,
            my_company_jobs=my_company_jobs,
            my_company_headcount=my_company_headcount,
            candidates=partner_candidates or acquire_candidates or build_candidates,
            rubric=rubric,
        )

        # 4. Generate reasoning for each path
        build_reasoning = synthesize_build_reasoning(args.my_company, analysis.build_analysis.score)
        partner_reasoning = synthesize_partner_reasoning(
            analysis.partner_analysis.candidates, analysis.partner_analysis.score
        )
        acquire_reasoning = synthesize_acquire_reasoning(
            analysis.acquire_analysis.candidates, analysis.acquire_analysis.score
        )

        # 5. Print output
        print(f"\n{'=' * 50}")
        print(f"STRATEGY ANALYSIS: {args.my_company} — {args.capability}")
        print(f"{'=' * 50}")
        print(f"\nBuild: {analysis.build_analysis.score:.1f}/10")
        print(f"  Timeline: {analysis.build_analysis.timeline_months} months")
        print(f"  Estimated cost: ${analysis.build_analysis.estimated_cost_usd:,}")
        print(f"  {build_reasoning}")
        print(f"\nPartner: {analysis.partner_analysis.score:.1f}/10")
        print(f"  Candidates: {len(analysis.partner_analysis.candidates)}")
        print(f"  {partner_reasoning}")
        print(f"\nAcquire: {analysis.acquire_analysis.score:.1f}/10")
        print(f"  Candidates: {len(analysis.acquire_analysis.candidates)}")
        print(f"  {acquire_reasoning}")

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
