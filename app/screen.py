"""Hard screening: pure Python, zero tokens.

This runs before any model call and is the main cost control in the app. It cuts
the full funder set down to a shortlist, so the matcher reasons over ~10 funders
instead of ~60. It also means a founder is never shown a funder whose own stated
rules disqualify them.

Two principles:

* An "unknown" answer never disqualifies. The funder stays in and the match is
  labelled needs_confirmation, because silently dropping a funder on a blank
  field is worse than showing it with a caveat.
* Preferences are not blockers. Only conditions of eligibility screen anyone out;
  preferences are left to the matcher to score.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models import FounderProfile

STAGE_ORDER = ["idea", "pre_seed", "seed", "series_a", "series_b_plus"]
REVENUE_FLOOR_USD = {
    "pre_revenue": 0, "under_100k": 1, "100k_500k": 100_000,
    "500k_2m": 500_000, "over_2m": 2_000_000,
}
# Which founder regulatory answers satisfy a funder's expectation.
REG_OK = {
    "none": {"*"},
    "pre_license_ok": {"*"},
    "license_in_progress": {"in_progress", "licensed", "sponsor_bank", "chartered", "none_needed"},
    "license_required": {"licensed", "sponsor_bank", "chartered", "none_needed"},
    "sponsor_bank_required": {"sponsor_bank", "chartered"},
    "charter_required": {"chartered"},
}
ATTRIBUTE_BLOCKERS = {"affiliation_required", "cdfi_certification_required"}

# Nothing shown to a founder should contain a raw enum value.
STAGE_LABEL = {
    "idea": "idea stage", "pre_seed": "pre-seed", "seed": "seed",
    "series_a": "Series A", "series_b_plus": "Series B+",
}
INSTRUMENT_LABEL = {
    "equity": "equity", "safe": "SAFEs", "convertible_note": "convertible notes",
    "grant": "grants", "prize": "prizes", "revenue_share": "revenue-based financing",
    "venture_debt": "venture debt", "warehouse_facility": "warehouse facilities",
    "recoverable_grant": "recoverable grants", "in_kind": "in-kind support",
}
VERTICAL_LABEL = {
    "banking_infra": "banking infrastructure", "embedded_finance": "embedded finance",
    "financial_health": "financial health", "financial_inclusion": "financial inclusion",
    "sme_finance": "SME finance", "not_fintech_specific": "fintech generally",
}


REG_LABEL = {
    "pre_license_ok": "is fine with pre-license companies",
    "license_in_progress": "expects license applications to be underway",
    "license_required": "requires you to be licensed already",
    "sponsor_bank_required": "requires a sponsor bank in place",
    "charter_required": "requires a bank charter",
}


def stage_label(stage: str) -> str:
    return STAGE_LABEL.get(stage, stage.replace("_", " "))


def vertical_label(vertical: str) -> str:
    return VERTICAL_LABEL.get(vertical, vertical.replace("_", " "))


def instrument_list(instruments) -> str:
    names = [INSTRUMENT_LABEL.get(i, i.replace("_", " ")) for i in sorted(instruments)]
    if len(names) <= 1:
        return names[0] if names else ""
    return f"{', '.join(names[:-1])} and {names[-1]}"


def stage_range(stages: list[str]) -> str:
    """"seed only" for a single stage, "pre-seed to Series A" for a span."""
    ordered = sorted(set(stages), key=STAGE_ORDER.index)
    if len(ordered) == 1:
        return f"{stage_label(ordered[0])} only"
    return f"{stage_label(ordered[0])} to {stage_label(ordered[-1])}"

# Financial inclusion is an orientation, not a product category: an inclusive
# lender is still a lender. Funders almost never tag themselves "financial
# inclusion" - they signal it through impact_mandate instead. So a founder who
# picks it must not be screened out of the lending and payments funders they are
# genuinely eligible for. These verticals count as compatible, never as a mismatch.
VERTICAL_COMPAT = {
    "financial_inclusion": {
        "financial_health", "lending", "payments", "remittances", "sme_finance",
    },
    "financial_health": {
        "financial_inclusion", "lending", "payments", "remittances", "sme_finance",
    },
}


@dataclass
class Screened:
    funder: dict
    eligible: bool
    excluded_by: list[str] = field(default_factory=list)
    needs_confirmation: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _known(value: str | None) -> bool:
    return bool(value) and value != "unknown"


def screen_one(funder: dict, profile: FounderProfile) -> Screened:
    out = Screened(funder=funder, eligible=True)

    def block(reason: str) -> None:
        out.eligible = False
        out.excluded_by.append(reason)

    codes = {b["code"] for b in funder.get("hard_blockers", [])}

    if "closed_program" in codes:
        block("program is closed")

    # --- stage ---
    stages = [s for s in (funder.get("stages") or []) if s in STAGE_ORDER]
    if stages and profile.stage not in stages:
        block(f"invests at {stage_range(stages)}; you are {stage_label(profile.stage)}")

    # --- vertical ---
    verticals = funder.get("fintech_verticals") or []
    if verticals and "not_fintech_specific" not in verticals:
        compatible = VERTICAL_COMPAT.get(profile.vertical, set())
        if profile.vertical not in verticals and not compatible.intersection(verticals):
            block(f"does not cover {vertical_label(profile.vertical)}")

    # --- instruments the founder is open to ---
    offered = set(funder.get("instruments") or [])
    if profile.open_to_instruments and offered:
        if not offered & set(profile.open_to_instruments):
            block(f"offers {instrument_list(offered)}, which you did not select")

    # --- revenue floor ---
    floor = funder.get("revenue_floor_usd")
    if floor:
        if not _known(profile.revenue):
            out.needs_confirmation.append(f"requires revenue of about ${floor:,}; you did not say")
        elif REVENUE_FLOOR_USD.get(profile.revenue, 0) < floor:
            block(f"requires about ${floor:,} revenue")
    elif funder.get("revenue_required") and profile.revenue == "pre_revenue":
        block("requires revenue; you are pre-revenue")

    # --- licensing / banking ---
    expectation = funder.get("regulatory_expectation") or "none"
    allowed = REG_OK.get(expectation, {"*"})
    if "*" not in allowed:
        if not _known(profile.regulatory_status):
            out.needs_confirmation.append(
                f"{REG_LABEL.get(expectation, expectation)}; you did not say where you stand")
        elif profile.regulatory_status not in allowed:
            block(REG_LABEL.get(expectation, expectation))

    # --- geography ---
    geos = [g.lower() for g in (funder.get("geographies") or [])]
    if geos and not any(g in ("global", "worldwide", "us", "usa", "united states") for g in geos):
        if profile.operating_geographies:
            if not {g.lower() for g in profile.operating_geographies} & set(geos):
                block(f"invests in {', '.join(funder['geographies'])}")

    # --- eligibility that depends on who the founder is ---
    for blocker in funder.get("hard_blockers", []):
        if blocker["code"] == "affiliation_required":
            if not [a for a in profile.founder_attributes if a != "none_or_private"]:
                block(blocker["description"])
            else:
                out.needs_confirmation.append(blocker["description"])
        elif blocker["code"] == "cdfi_certification_required":
            out.needs_confirmation.append(blocker["description"])
        elif blocker["code"] in {"no_cold_inbound", "portfolio_conflict"}:
            out.warnings.append(blocker["description"])
        elif blocker["code"] not in ATTRIBUTE_BLOCKERS and out.eligible:
            # Any blocker we cannot evaluate structurally is surfaced, not applied.
            out.warnings.append(blocker["description"])

    # --- balance-sheet lending: a routing signal, never a blocker ---
    if profile.lends_own_balance_sheet in {"yes", "planning"} and "warehouse_facility" in offered:
        out.warnings.append("relevant to funding your loan book, not your operations")

    return out


def screen_all(funders: list[dict], profile: FounderProfile) -> tuple[list[Screened], list[Screened]]:
    """Returns (eligible, excluded). Both are kept so the UI can show the no's."""
    results = [screen_one(f, profile) for f in funders]
    return [r for r in results if r.eligible], [r for r in results if not r.eligible]


def prerank(screened: list[Screened], profile: FounderProfile, limit: int) -> list[Screened]:
    """Cheap ranking to pick the shortlist the matcher sees. Pure Python, no tokens.

    This is the cost lever: it decides how many funders reach the model.
    """

    def score(item: Screened) -> tuple:
        f = item.funder
        points = 0
        verticals = f.get("fintech_verticals") or []
        if profile.vertical in verticals:
            points += 3
        elif "not_fintech_specific" in verticals:
            points += 1
        if set(f.get("instruments") or []) & set(profile.open_to_instruments):
            points += 2
        if profile.populations_served and f.get("impact_mandate") in {"required", "preferred"}:
            points += 2
        if f.get("actively_deploying") is True:
            points += 2
        elif f.get("actively_deploying") is False:
            points -= 3
        if profile.stage in (f.get("stages") or []):
            points += 2
        if f.get("stated_criteria"):
            points += 1
        points += lending_boost(item, profile)
        points -= len(item.needs_confirmation)
        return (points, len(f.get("stated_criteria") or []))

    return sorted(screened, key=score, reverse=True)[:limit]


def lending_boost(item: Screened, profile: FounderProfile) -> int:
    """A founder who lends off their own balance sheet needs loan-book capital.

    Without this the debt providers rank below equity funds, because their pages
    say far less than a VC's does. The need is real, so the routing is explicit.
    """
    if profile.lends_own_balance_sheet not in {"yes", "planning"}:
        return 0
    instruments = set(item.funder.get("instruments") or [])
    if "warehouse_facility" in instruments:
        return 6
    if "venture_debt" in instruments:
        return 3
    return 0
