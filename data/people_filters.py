"""Filters for cleaning up raw Crustdata people / decision-maker responses.

Crustdata's `people.decision_makers` and `people.founders` arrays are noisy:
job titles contain the word "Partner" in a channel/talent sense rather than a
seniority sense, and founders of acquired subsidiaries or unrelated companies
leak in. This module drops the noise while keeping genuine senior
decision-makers.
"""

from __future__ import annotations

import re
from typing import NamedTuple

# Substring-matched (case-insensitively) against a person's current_title.
# "head" (not just "head of") covers "Global Head", "Regional Head", etc.
SENIOR_KEYWORDS = (
    "chief",
    "vp",
    "vice president",
    "head",
    "director",
    "managing director",
    "founder",
    "co-founder",
    "ceo",
    "cto",
    "coo",
    "cfo",
)

# Titles matching these get an extra cross-check that the company they're
# associated with is actually the target, not a different one.
FOUNDER_KEYWORDS = ("founder", "co-founder")

# Extracts a company name from patterns like "@ Company", "at Company", "of Company".
_COMPANY_REF = re.compile(
    r"(?:@|at|of)\s+([A-Za-z0-9][\w&\-\s]*?)(?=\s*[,\|\-–—]|\s*$)",
    re.IGNORECASE,
)

# Corporate suffixes stripped when normalizing a company name for comparison.
_COMPANY_SUFFIXES = (
    "inc",
    "inc.",
    "ltd",
    "ltd.",
    "llc",
    "co",
    "co.",
    "company",
    "corporation",
    "corp",
    "corp.",
)


class FilterResult(NamedTuple):
    people: list[dict]
    filtered_out_count: int


def _normalize_company(name: str) -> str:
    """Lowercase, strip, and remove common corporate suffixes."""
    cleaned = name.strip().lower()
    parts = [p for p in cleaned.split() if p.rstrip(".") not in _COMPANY_SUFFIXES]
    return " ".join(parts).strip()


def _company_name_from_domain(domain: str) -> str:
    """'stripe.com' -> 'stripe'."""
    return _normalize_company(domain.split(".")[0])


def _extract_referenced_company(title: str) -> str | None:
    """Return the primary company referenced in a title, if any."""
    match = _COMPANY_REF.search(title)
    if not match:
        return None
    return _normalize_company(match.group(1))


def _references_different_company(title: str, target_name: str) -> bool:
    """True if the title references a company other than the target."""
    referenced = _extract_referenced_company(title)
    if referenced is None:
        return False  # no company referenced -> can't prove it's different
    return (
        referenced != target_name
        and target_name not in referenced
        and referenced not in target_name
    )


def _has_senior_keyword(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in SENIOR_KEYWORDS)


def _is_founder_title(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in FOUNDER_KEYWORDS)


def filter_decision_makers(
    people_list: list[dict],
    target_company_domain: str,
) -> FilterResult:
    """Filter a raw Crustdata people list down to genuine senior decision-makers.

    Rules:
      1. Keep only titles matching a senior keyword (C-suite, VP, Head,
         Director, Founder, etc.).
      2. Titles containing "Partner" are kept only if they also match a senior
         keyword (e.g. "Head of ... Partner Marketing" stays; "Talent Partner"
         goes). This falls out of rule 1 because "partner" is not itself a
         senior keyword.
      3. Founder-type titles get a cross-check: if the title references a
         company other than the target, it is dropped (founded a different
         company or a subsidiary Stripe acquired).
    """
    target_name = _company_name_from_domain(target_company_domain)

    kept: list[dict] = []
    filtered_out = 0

    for person in people_list:
        basic = person.get("basic_profile") or {}
        title = (basic.get("current_title") or "").strip()

        if not title or not _has_senior_keyword(title):
            filtered_out += 1
            continue

        if _is_founder_title(title) and _references_different_company(title, target_name):
            filtered_out += 1
            continue

        kept.append(person)

    return FilterResult(people=kept, filtered_out_count=filtered_out)
