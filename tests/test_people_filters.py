import json
from pathlib import Path

import pytest

from data.people_filters import filter_decision_makers

FIXTURE = (
    Path(__file__).parent / "fixtures" / "company_enrich_real_stripe_people_raw.json"
)

STRIPE_DOMAIN = "stripe.com"


@pytest.fixture
def raw_people() -> list[dict]:
    data = json.loads(FIXTURE.read_text())
    # Filter operates on the union of both arrays, as the scoring layer would.
    return data["decision_makers"] + data["founders"]


@pytest.fixture
def result(raw_people: list[dict]) -> "filter_decision_makers.__annotations__":  # noqa: F821
    return filter_decision_makers(raw_people, STRIPE_DOMAIN)


@pytest.fixture
def kept(result) -> list[dict]:
    return result.people


@pytest.fixture
def kept_names(kept: list[dict]) -> set[str]:
    return {p["basic_profile"]["name"] for p in kept}


# ── Filtered-out assertions ─────────────────────────────────────


def test_leak_stash_filtered_out(kept_names: set[str]) -> None:
    """Founder @ Leakstash — Stripe mentioned only incidentally."""
    assert "Leak Stash" not in kept_names


def test_asta_l_filtered_out(kept_names: set[str]) -> None:
    """Co-Founder & CTO at Privy, a Stripe Company — founded a subsidiary, not Stripe."""
    assert "Asta L." not in kept_names


@pytest.mark.parametrize(
    "name",
    [
        # Talent / HR Partner roles — no senior keyword.
        "Swati Tomar",
        "Saumya Parashar",
        "Vishal Chowdri",
        "Zafar A",
        "Pronoti Roy",
        "Sarah Tobin",
        "Omer  Khalid",
        # Partner Development / Sales / Marketing roles — no senior keyword.
        "Jamie Heaslip",
        "Desirée Choquette",
        "Sadie Depew Perrotta",
        "Sam Dines",
        "Giancarlo Laudini",
        "Niamh Linehan",
        "Marya Kato",
        "Aleksandar Kleindopp",
        "Lauren C.",
        "Dimitri Sedashev",
        "Alexandru Stefan",
        "Sarah Anne Swiss",
        "Samar M.",
        "Dominick-Dante (Cam) Dixon",
        "Marie-Anne GOMEZ",
        "Shawn Durrani",
        "Dave O Leary",
        "Lynette Chong",
        "Jing Yi Tan",
        "Lorna Leydon",
        "Davide Pellegrini",
        "Nikhil Gupta",
        "Bonnie Macqueen",
        "Michael Magabo",
        "Danna Gil",
        "Will Reale",
        "Alex Godfrey",
        "Kimiko Fujioka Guillermo",
        "Anoushka Wunsch",
        # VC / Startup Partner Lead — no senior keyword.
        "Pranav Ashok",
    ],
)
def test_partner_only_titles_filtered_out(name: str, kept_names: set[str]) -> None:
    """Every 'Partner' title without a seniority keyword is dropped."""
    assert name not in kept_names, f"{name} should have been filtered out"


# ── Kept assertions ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "name",
    [
        # C-suite
        "Eileen O'Mara",  # Chief Revenue Officer
        "John Beauchamp",  # Chief Revenue Officer
        "Tyler Bryson",  # Chief Revenue Officer
        "Ed Morris",  # Chief Revenue Officer
        "Maia Josebachvili",  # Chief Revenue Officer of AI
        "Paul H.",  # Chief Revenue Officer
        "Ravi Adusumilli",  # Chief Revenue Officer
        "Jeff Titterton",  # Chief Marketing Officer
        "Steffan Tomlinson",  # CFO
        "Jurgen Van Gael",  # CTO & Board Member
        "Barbara O'Beirne",  # CEO Stripe Technology Europe
        "Vishnu Challam",  # CEO and Whole Time Director — Stripe India
        "Robert McIntosh",  # Chief People Officer
        "Fran Ryan",  # Chief Business Officer
        "Clara Liang",  # Chief Business Operations Officer
        "Scott Farrington",  # Chief Accounting Officer
        "Nick Colón",  # Chief Integrity Officer
        # Heads
        "Matthias Lecroix",  # Head of Sales
        "Stephanie J. Neill",  # Head of Product
        "Dave Nixon",  # Global Head of Sales Development
        "Brayden McCarthy",  # Head of Product
        "Kanchan Belavadi",  # Head of Marketing
        "Jon Murrell",  # VP of Growth
        "Abhinav S.",  # Vice President of Product Development
        # Directors
        "Henry Swarbrick",  # Regional Director
        "Karl Durrance",  # Managing Director
        "Davina Saint",  # Independent Non Executive Director
        "Alicia Gill",  # Senior Director
        "Maggie Nelson",  # Director of Engineering
        "Annie Bohlander",  # Director of Sales
        # Senior partner titles (kept because they ALSO match a senior keyword)
        "Julie D. Jacobson",  # Head of Global Alliances and Regional Partner Marketing
        "Kamal Arora",  # Global Head - Partner Solutions Architecture
        "Amy Brito",  # Head of Alliances & Channels Partner Development
    ],
)
def test_genuine_senior_people_kept(name: str, kept_names: set[str]) -> None:
    assert name in kept_names, f"{name} should have been kept"


# ── Known limitations (documented, not bugs) ────────────────────


def test_president_not_in_keyword_list_is_filtered(kept_names: set[str]) -> None:
    """'President' is not in the spec's senior keyword list, so William Gaybrick
    ('President, Technology and Business') is dropped. He IS a real senior exec —
    this is a gap in the keyword list, reported here as a finding."""
    assert "William Gaybrick" not in kept_names


def test_bare_founder_titles_kept(kept_names: set[str]) -> None:
    """Founders with no company reference can't be cross-checked, so they pass.
    These are likely noise (random founders in the CRM), but the filter has no
    basis to exclude them without a company to compare against."""
    assert "Pál Klaudia" in kept_names  # "Founder" — no company
    assert "Finlay Glenn" in kept_names  # "Founder" — no company


def test_substring_match_can_false_positive(kept_names: set[str]) -> None:
    """'A. Yancey, PHR' is an Administrative Business Partner whose title happens
    to contain 'Head of' ('...to the Head of Solutions Architecture'). Substring
    matching keeps her. This is an inherent limitation of keyword matching."""
    assert "A. Yancey, PHR" in kept_names  # false positive — documented


# ── Reporting ───────────────────────────────────────────────────


def test_genuine_senior_people_exist_after_filtering(kept_names: set[str]) -> None:
    """The whole point: after filtering, real senior Stripe people remain."""
    assert "Eileen O'Mara" in kept_names  # CRO
    assert "Steffan Tomlinson" in kept_names  # CFO
    assert "Jurgen Van Gael" in kept_names  # CTO


def test_filter_transparently_reports_counts(result, raw_people: list[dict]) -> None:
    total = len(raw_people)
    kept = len(result.people)
    print(
        f"\nFilter result: {kept} kept, {result.filtered_out_count} "
        f"filtered out of {total} total"
    )
    assert result.filtered_out_count == total - kept


def test_print_survivors(kept: list[dict]) -> None:
    """Print every surviving name + title for manual review."""
    print("\nSurvivors after filtering:")
    for p in kept:
        bp = p["basic_profile"]
        print(f"  {bp['name']}: {bp['current_title']}")
