import argparse

from data.caching_client import CachingClient
from llm.synthesize import classify_goal, synthesize_narrative
from scoring.engine import Evidence, build_output, score_all
from scoring.rubric_loader import load_rubric


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build vs Partner vs Acquire Decision Engine"
    )
    parser.add_argument(
        "--goal", required=True, help="e.g. 'We want to enter AI voice'"
    )
    parser.add_argument(
        "--target-company", required=True, help="e.g. 'Stripe'"
    )
    parser.add_argument(
        "--requesting-company", default=None, help="Your company name (optional)"
    )
    args = parser.parse_args()

    try:
        # 1. Classify goal → capability tags
        print(f"\n📊 Analyzing: {args.goal}")
        print(f"Target: {args.target_company}")
        print("\nClassifying goal...")
        classification = classify_goal(args.goal)
        print(f"Capability tags: {', '.join(classification.taxonomy_tags)}")

        # 2. Fetch target company data
        print(f"\nFetching {args.target_company} data...")
        caching_client = CachingClient()
        target_data, provenance = caching_client.get_company_enrichment(
            args.target_company
        )
        print(f"Data fetched (cache_hit={provenance.cache_hit})")

        # 3. Build evidence and score all 3 paths
        print("\nScoring all 3 paths...")
        rubric = load_rubric("rubric.yaml")
        evidence = Evidence(
            taxonomy_tags=classification.taxonomy_tags,
            own_enrichment=target_data,
            candidate_enrichment=target_data,
            acquire_enrichment=target_data,
            api_call_ids={
                "own_enrichment": provenance.api_call_id,
                "candidate_enrichment": provenance.api_call_id,
                "acquire_enrichment": provenance.api_call_id,
            },
        )
        scores = score_all(rubric, evidence)

        # 4. Build output & pick recommendation
        output = build_output(scores, rubric)

        # 5. Generate narrative
        top_path = output.recommendation.primary_path
        top_path_score = next(s for s in scores if s.path == top_path)
        print("Generating recommendation narrative...")
        narrative = synthesize_narrative(
            top_path_score,
            output.final_scores,
            args.target_company,
        )

        # 6. Print output
        print(f"\n{'=' * 50}")
        print(f"RECOMMENDATION: {top_path.upper()}")
        print(f"Score: {top_path_score.score:.1f}/10")
        print(f"Close call: {output.recommendation.is_close_call}")
        print(f"{'=' * 50}")
        print(f"\n{narrative}")
        print("\nEvidence breakdown:")
        for criterion in top_path_score.criteria:
            if criterion.evidence:
                print(
                    f"  • {criterion.criterion_id}: "
                    f"{criterion.evidence.raw_value} → {criterion.score:.1f}/10"
                )

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
