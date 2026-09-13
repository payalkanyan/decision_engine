import argparse


def main() -> None:
    """CLI entry point for demos.

    Orchestrates: classify → fetch/cache → score → synthesize → print.
    Usage:
        python -m cli.main --goal "We want to enter AI voice" --dry-run
        python -m cli.main --goal "We want to enter AI voice"
    """
    parser = argparse.ArgumentParser(
        description="Build vs Partner vs Acquire decision engine"
    )
    parser.add_argument(
        "--goal", required=True, help="Strategic capability goal (e.g. 'enter AI voice')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use cached/mock data only — no live API calls",
    )
    parser.add_argument(
        "--company",
        default=None,
        help="Requesting company name (for build-path self-analysis)",
    )

    args = parser.parse_args()

    # Pipeline: classify → fetch/cache → score → synthesize → print
    raise NotImplementedError(f"Pipeline not yet implemented for goal: {args.goal}")


if __name__ == "__main__":
    main()
