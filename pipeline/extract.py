"""Turn a funder's cached page text into a structured record.

One LLM call per funder (gpt-6-luna through Portkey, Responses API, structured
output). The model may only report what the page says; every factual field it
fills must come with the exact sentence it came from.

Those quotes are then checked in plain Python against the cached text. A quote
that is not in the source is a fabrication, and the field is dropped and sent to
the review queue. That check costs zero tokens.
"""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

from config import MODEL_NAME, USAGE_LOG, get_client

Category = Literal[
    "equity_vc", "accelerator", "corporate_accelerator", "grant", "grant_challenge",
    "fellowship", "government", "revenue_based", "venture_debt", "debt_warehouse",
    "debt_marketplace", "debt_infra", "debt", "in_kind", "corporate_impact",
]
Instrument = Literal[
    "equity", "safe", "convertible_note", "grant", "prize", "revenue_share",
    "venture_debt", "warehouse_facility", "recoverable_grant", "in_kind",
]
Stage = Literal["idea", "pre_seed", "seed", "series_a", "series_b_plus"]
Vertical = Literal[
    "lending", "payments", "banking_infra", "embedded_finance", "insurtech", "wealth",
    "regtech", "financial_health", "remittances", "sme_finance", "crypto", "not_fintech_specific",
]
BlockerCode = Literal[
    "geo_restricted", "stage_floor", "stage_ceiling", "revenue_floor", "entity_type",
    "nonprofit_only", "for_profit_only", "license_required", "sponsor_bank_required",
    "excluded_vertical", "portfolio_conflict", "no_cold_inbound",
    "cdfi_certification_required", "affiliation_required", "closed_program",
]


class Blocker(BaseModel):
    code: BlockerCode
    description: str = Field(description="One line, plain English, what it disqualifies")
    source_quote: str = Field(description="Exact sentence from the page proving this is a rule")


class Cited(BaseModel):
    """A value the page actually states, with the sentence that states it."""

    value: str
    source_quote: str


class FunderExtract(BaseModel):
    category: Category
    instruments: list[Instrument]
    stages: list[Stage]
    check_size_min_usd: Optional[int] = None
    check_size_max_usd: Optional[int] = None
    check_size_quote: Optional[str] = None
    geographies: list[str]
    fintech_verticals: list[Vertical]
    impact_mandate: Literal["required", "preferred", "none"]
    impact_reporting_standard: list[str]
    thesis_summary: str = Field(max_length=300)
    stated_criteria: list[Cited]
    hard_blockers: list[Blocker]
    regulatory_expectation: Literal[
        "none", "pre_license_ok", "license_in_progress", "license_required",
        "sponsor_bank_required", "charter_required",
    ]
    revenue_required: bool
    revenue_floor_usd: Optional[int] = None
    application_mode: Literal["open_application", "rolling", "deadline_based", "warm_intro_only"]
    application_url: Optional[str] = None
    page_supports_extraction: bool = Field(
        description="False if the page did not actually describe this funder's criteria"
    )


SYSTEM = """You extract funder eligibility data from a funder's own web pages.

Rules:
- Report ONLY what the supplied text says. You have no outside knowledge of this funder.
- Every source_quote must be copied VERBATIM from the supplied text. Never paraphrase a quote.
- If the text does not state something, leave it null or use an empty list. Do not guess.
- hard_blockers are CONDITIONS OF ELIGIBILITY only ("must", "only", "required", "we do not fund").
  A preference ("we emphasize", "most of our companies are") is NOT a blocker: put it in
  stated_criteria instead.
- Set page_supports_extraction=false if the text is a cookie notice, an error page, or
  otherwise does not describe this funder.
- check_size_quote must be the sentence that states those dollar figures. If no sentence
  states a check size, leave all three check-size fields null.
- stages: list ONLY the stages the page names. Do not list every stage as a default.
- fintech_verticals: use "not_fintech_specific" ALONE when the funder is not fintech-focused.
  Never combine it with named verticals."""


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _quote_in_source(quote: str, source_norm: str) -> bool:
    """A quote counts as real if it appears in the page text once normalised."""
    q = _norm(quote)
    if len(q) < 12:
        return False
    if q in source_norm:
        return True
    # Tolerate minor truncation at the edges of a long quote.
    words = q.split()
    if len(words) >= 10:
        return " ".join(words[2:-2]) in source_norm
    return False


_AMOUNT = re.compile(
    r"\$\s?([\d,]+(?:\.\d+)?)\s*(k|m|mm|bn|b|thousand|million|billion)?", re.IGNORECASE
)
_MULT = {
    "k": 1_000, "thousand": 1_000, "m": 1_000_000, "mm": 1_000_000,
    "million": 1_000_000, "b": 1_000_000_000, "bn": 1_000_000_000,
    "billion": 1_000_000_000,
}


def _amounts_in(text: str) -> set[int]:
    """Dollar figures the sentence actually contains, normalised to whole dollars."""
    found: set[int] = set()
    for number, suffix in _AMOUNT.findall(text or ""):
        try:
            value = float(number.replace(",", ""))
        except ValueError:
            continue
        found.add(int(value * _MULT.get((suffix or "").lower(), 1)))
    return found


def _value_supported(value: Optional[int], quote: Optional[str]) -> bool:
    """A number is only kept if its own quote states that number.

    Catches the case where the model attaches a real sentence to an invented
    figure - the quote check alone passes, but the quote does not back the value.
    """
    if value is None:
        return True
    return value in _amounts_in(quote or "")


def _log_usage(funder_id: str, usage) -> dict:
    details = getattr(usage, "input_tokens_details", None)
    record = {
        "stage": "extract",
        "funder_id": funder_id,
        "model": MODEL_NAME,
        "input_tokens": usage.input_tokens,
        "cached_input_tokens": getattr(details, "cached_tokens", 0) or 0,
        "output_tokens": usage.output_tokens,
    }
    USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with USAGE_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    return record


def extract_funder(funder_id: str, name: str, page_text: str, pages: list[str]) -> dict:
    """One LLM call. Returns a record dict plus a list of dropped (unsupported) quotes."""
    client = get_client()
    response = client.responses.parse(
        model=MODEL_NAME,
        instructions=SYSTEM,
        input=f"Funder: {name}\n\n--- PAGE TEXT ---\n{page_text}",
        text_format=FunderExtract,
        reasoning={"effort": "low"},
    )
    usage = _log_usage(funder_id, response.usage)
    data = response.output_parsed

    # Zero-token fabrication check: every quote must exist in the page we fetched.
    source_norm = _norm(page_text)
    dropped: list[str] = []

    kept_criteria = []
    for item in data.stated_criteria:
        if _quote_in_source(item.source_quote, source_norm):
            kept_criteria.append(item.model_dump())
        else:
            dropped.append(f"stated_criteria: {item.source_quote[:90]}")

    kept_blockers = []
    for blocker in data.hard_blockers:
        if _quote_in_source(blocker.source_quote, source_norm):
            kept_blockers.append(blocker.model_dump())
        else:
            dropped.append(f"hard_blocker[{blocker.code}]: {blocker.source_quote[:90]}")

    record = data.model_dump()
    record["stated_criteria"] = kept_criteria
    record["hard_blockers"] = kept_blockers

    quote = data.check_size_quote
    if data.check_size_min_usd is not None or data.check_size_max_usd is not None:
        if not quote or not _quote_in_source(quote, source_norm):
            dropped.append(f"check_size quote not in page: {(quote or '(none)')[:90]}")
            ok = False
        elif not (
            _value_supported(data.check_size_min_usd, quote)
            and _value_supported(data.check_size_max_usd, quote)
        ):
            dropped.append(
                f"check_size {data.check_size_min_usd}-{data.check_size_max_usd} "
                f"not stated in its own quote: {quote[:90]}"
            )
            ok = False
        else:
            ok = True
        if not ok:
            record["check_size_min_usd"] = None
            record["check_size_max_usd"] = None
            record["check_size_quote"] = None

    if record["revenue_floor_usd"] is not None and not _amounts_in(
        " ".join(c["source_quote"] for c in kept_criteria)
        + " ".join(b["source_quote"] for b in kept_blockers)
    ):
        dropped.append(f"revenue_floor {record['revenue_floor_usd']} unsupported by any quote")
        record["revenue_floor_usd"] = None

    record.update(
        {
            "funder_id": funder_id,
            "name": name,
            "source_pages": pages,
            "last_verified": date.today().isoformat(),
            "dropped_unsupported": dropped,
            "usage": usage,
            # Tier B - filled in by hand, never by the model.
            "decision_timeline_weeks": None,
            "reporting_hours_per_quarter": None,
            "ops_support": None,
            "ops_support_detail": None,
            "actively_deploying": None,
            "founder_notes": None,
            "confidence": "unknown",
        }
    )
    return record
