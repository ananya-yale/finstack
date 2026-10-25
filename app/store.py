"""Load the funder dataset: extracted facts + hand-entered judgment.

data/funders.json       - built by the pipeline, every fact carries a quote.
data/tier_b.csv         - filled in by hand. Never touched by the pipeline, so a
                          re-run of the extraction cannot overwrite it.

Merged here at load time. Each field keeps its provenance ("cited" or
"practitioner") so the UI and the report can always say where a number came from.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FUNDERS_JSON = ROOT / "data" / "funders.json"
TIER_B_CSV = ROOT / "data" / "tier_b.csv"
SEED_CSV = ROOT / "data" / "funder_seed_list.csv"

# Most debt and grant providers never spell out their instrument in words a page
# can be quoted on ("we provide warehouse facilities"). Their category in our own
# seed list does say it, so we derive the instrument from that rather than leave
# the field empty. Marked "derived" in provenance - not a quote, not a guess.
CATEGORY_INSTRUMENTS = {
    "debt_warehouse": ["warehouse_facility"],
    "debt_infra": ["warehouse_facility"],
    "debt_marketplace": ["venture_debt", "warehouse_facility"],
    "debt": ["venture_debt", "warehouse_facility"],
    "venture_debt": ["venture_debt"],
    "revenue_based": ["revenue_share"],
    "grant": ["grant"],
    "grant_challenge": ["grant", "prize"],
    "government": ["grant"],
    "fellowship": ["grant"],
    "in_kind": ["in_kind"],
    "accelerator": ["equity", "safe", "in_kind"],
    "corporate_accelerator": ["in_kind"],
    "equity_vc": ["equity", "safe"],
    "equity_fintech": ["equity", "safe"],
    "equity_generalist": ["equity", "safe"],
    "equity_impact": ["equity", "safe"],
    "corporate_impact": ["equity"],
}


def load_seed_categories() -> dict[str, str]:
    """Categories for funders still marked keep=y. Dropping a row from the seed
    list removes it from the app, without rebuilding funders.json."""
    if not SEED_CSV.exists():
        return {}
    with SEED_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return {
            r["id"]: r.get("category", "")
            for r in csv.DictReader(handle)
            if r.get("id") and (r.get("keep") or "").strip().lower() == "y"
        }

TIER_B_FIELDS = [
    "actively_deploying",
    "regulatory_expectation",
    "decision_timeline_weeks",
    "reporting_hours_per_quarter",
    "ops_support",
    "ops_support_detail",
    "founder_notes",
    "confidence",
]
# Extracted fields a practitioner may also fill when the page did not state them.
PRACTITIONER_GAPS = ["stages", "check_size_min_usd", "check_size_max_usd",
                     "fintech_verticals"]

_INT_FIELDS = {"decision_timeline_weeks", "reporting_hours_per_quarter",
               "check_size_min_usd", "check_size_max_usd"}
_BOOL = {"yes": True, "y": True, "true": True, "no": False, "n": False, "false": False}


def _coerce(field: str, raw: str):
    value = (raw or "").strip()
    if not value or value.lower() in {"unknown", "na", "n/a", "-"}:
        return None
    if field == "actively_deploying":
        return _BOOL.get(value.lower())
    if field in _INT_FIELDS:
        try:
            return int(float(value.replace(",", "").replace("$", "")))
        except ValueError:
            return None
    if field in {"stages", "fintech_verticals"}:
        return [s.strip() for s in value.split("|") if s.strip()]
    return value


def load_tier_b() -> dict[str, dict]:
    if not TIER_B_CSV.exists():
        return {}
    with TIER_B_CSV.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    out: dict[str, dict] = {}
    for row in rows:
        fid = (row.get("funder_id") or "").strip()
        if not fid:
            continue
        filled = {}
        for field in TIER_B_FIELDS + PRACTITIONER_GAPS:
            value = _coerce(field, row.get(field, ""))
            if value is not None:
                filled[field] = value
        out[fid] = filled
    return out


def load_funders() -> list[dict]:
    tier_b = load_tier_b()
    categories = load_seed_categories()
    funders = [
        f for f in json.loads(FUNDERS_JSON.read_text(encoding="utf-8"))
        if f["funder_id"] in categories
    ]

    for funder in funders:
        overlay = tier_b.get(funder["funder_id"], {})
        provenance = {}

        if overlay.get("fintech_verticals"):
            funder["fintech_verticals"] = overlay["fintech_verticals"]
            provenance["fintech_verticals"] = "practitioner"

        for field in PRACTITIONER_GAPS:
            if field == "fintech_verticals":
                continue
            if funder.get(field) in (None, [], ""):
                if field in overlay:
                    funder[field] = overlay[field]
                    provenance[field] = "practitioner"
            else:
                provenance[field] = "cited"

        for field in TIER_B_FIELDS:
            funder[field] = overlay.get(field, funder.get(field))
            if overlay.get(field) is not None:
                provenance[field] = "practitioner"

        # regulatory_expectation is judgment, not something funders publish.
        # Anything the extractor guessed is discarded unless a human confirmed it.
        if provenance.get("regulatory_expectation") != "practitioner":
            funder["regulatory_expectation"] = None

        funder["seed_category"] = categories.get(funder["funder_id"], "")
        if not funder.get("instruments"):
            derived = CATEGORY_INSTRUMENTS.get(funder["seed_category"], [])
            if derived:
                funder["instruments"] = derived
                provenance["instruments"] = "derived"
        else:
            provenance["instruments"] = "cited"

        funder.setdefault("confidence", "unknown")
        funder["provenance"] = provenance
        funder["assessed"] = any(
            overlay.get(f) is not None for f in TIER_B_FIELDS if f != "confidence"
        )

    return funders


def coverage(funders: list[dict]) -> dict:
    """Honest counts for the UI footer and the report."""
    return {
        "total": len(funders),
        "assessed": sum(1 for f in funders if f["assessed"]),
        "with_stages": sum(1 for f in funders if f.get("stages")),
        "with_check_size": sum(
            1 for f in funders if f.get("check_size_min_usd") or f.get("check_size_max_usd")
        ),
    }
