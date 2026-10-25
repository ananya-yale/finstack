"""The founder profile, and the shapes the agents return.

Field names and allowed values mirror docs/intake_spec.md. Anything the founder
did not answer stays "unknown", which the filter treats as "do not disqualify".
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Stage = Literal["idea", "pre_seed", "seed", "series_a", "series_b_plus"]
Vertical = Literal[
    "lending", "payments", "banking_infra", "embedded_finance", "insurtech", "wealth",
    "regtech", "financial_health", "financial_inclusion", "remittances", "sme_finance",
    "crypto",
]
Entity = Literal[
    "delaware_c_corp", "other_c_corp", "llc", "pbc", "nonprofit", "not_incorporated", "unknown"
]
Revenue = Literal["pre_revenue", "under_100k", "100k_500k", "500k_2m", "over_2m", "unknown"]
RegStatus = Literal[
    "none_needed", "none_yet", "in_progress", "licensed", "sponsor_bank", "chartered", "unknown"
]
Instrument = Literal[
    "equity", "safe", "convertible_note", "grant", "prize", "revenue_share",
    "venture_debt", "warehouse_facility", "recoverable_grant", "in_kind",
]
Served = Literal[
    "lmi_households", "thin_file", "immigrants", "small_businesses", "rural", "none_specifically"
]
Support = Literal["bank_intros", "regulatory_help", "hiring", "distribution", "none"]
Attribute = Literal[
    "current_student", "underrepresented_founder", "university_affiliation", "none_or_private"
]


class FounderProfile(BaseModel):
    """What the matcher needs. Built by the intake agent from the form + free text."""

    # Q1-Q3
    stage: Stage
    description: str = Field(max_length=600)
    vertical: Vertical

    # Q4-Q5
    entity_type: Entity = "unknown"
    incorporation_state: Optional[str] = None
    operating_geographies: list[str] = Field(default_factory=list)
    operates_outside_us: bool = False

    # Q6-Q8
    revenue: Revenue = "unknown"
    regulatory_status: RegStatus = "unknown"
    lends_own_balance_sheet: Literal["yes", "no", "planning", "unknown"] = "unknown"

    # Q9-Q11
    capital_sought_usd: Optional[int] = None
    use_of_funds: list[str] = Field(default_factory=list)
    open_to_instruments: list[Instrument] = Field(default_factory=list)
    timeline: Literal["under_1_month", "1_3_months", "3_6_months", "6_plus_months", "unknown"] = (
        "unknown"
    )

    # Q12-Q14
    populations_served: list[Served] = Field(default_factory=list)
    impact_note: Optional[str] = None
    support_needed: list[Support] = Field(default_factory=list)
    founder_attributes: list[Attribute] = Field(default_factory=list)

    # Provenance: which fields the agent inferred rather than being told directly.
    # The UI shows these back to the founder for correction.
    inferred_fields: list[str] = Field(default_factory=list)
    # Filter-critical fields still blank, with what each one costs.
    missing_filter_fields: list[str] = Field(default_factory=list)


class FollowUp(BaseModel):
    question: str
    field: str
    why_it_matters: str


class IntakeResult(BaseModel):
    profile: FounderProfile
    follow_ups: list[FollowUp] = Field(max_length=3, default_factory=list)
