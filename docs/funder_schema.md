# Funder record schema (draft)

One JSON object per funder. Two kinds of fields:

- **Tier A — extracted.** Pulled from the funder's own pages by the pipeline. Every Tier A field must carry a source URL and the exact quote it came from. If no quote supports it, the field is `null`, never a guess.
- **Tier B — judgment.** Not published anywhere. You fill these in, and only for funders you actually know. Everything else stays `null` with `confidence: "unknown"`, and the app says "not assessed" rather than inventing a number.

---

## Tier A — extracted with citation

| Field | Type | Notes |
|---|---|---|
| `funder_id` | string | stable slug, matches the seed list |
| `name` | string | |
| `url` | string | primary page used for extraction |
| `category` | enum | `equity_vc`, `accelerator`, `corporate_accelerator`, `grant`, `grant_challenge`, `fellowship`, `government`, `revenue_based`, `venture_debt`, `debt_warehouse`, `in_kind` |
| `instruments` | list[enum] | `equity`, `safe`, `convertible_note`, `grant`, `prize`, `revenue_share`, `venture_debt`, `warehouse_facility`, `recoverable_grant`, `in_kind` |
| `stages` | list[enum] | `idea`, `pre_seed`, `seed`, `series_a`, `series_b_plus` |
| `check_size_min_usd` | int | null if unstated |
| `check_size_max_usd` | int | null if unstated |
| `geographies` | list[string] | e.g. `US`, `US-CA`, `Global`, `Sub-Saharan Africa` |
| `fintech_verticals` | list[enum] | `lending`, `payments`, `banking_infra`, `embedded_finance`, `insurtech`, `wealth`, `regtech`, `financial_health`, `remittances`, `sme_finance`, `crypto` |
| `impact_mandate` | enum | `required`, `preferred`, `none` |
| `impact_reporting_standard` | list[string] | e.g. `IRIS+`, `B Corp`, `custom`, `none` |
| `thesis_summary` | string | ≤300 chars, paraphrased from their own words |
| `stated_criteria` | list[string] | direct quotes of what they say they look for |
| `hard_blockers` | list[object] | see below — the most important field in the schema |
| `regulatory_expectation` | enum | `none`, `pre_license_ok`, `license_in_progress`, `license_required`, `sponsor_bank_required`, `charter_required` |
| `revenue_required` | bool | |
| `revenue_floor_usd` | int | null if none stated |
| `application_mode` | enum | `open_application`, `rolling`, `deadline_based`, `warm_intro_only` |
| `deadlines` | list[object] | `{name, date, recurring: bool}` |
| `application_url` | string | |
| `sources` | object | `field_name -> {url, quote, retrieved_at}` for every field above |
| `last_verified` | date | |

### `hard_blockers` object

```json
{
  "code": "license_required",
  "description": "Will not fund pre-license money transmitters",
  "source_quote": "Companies must hold applicable state licenses prior to investment.",
  "source_url": "https://example.com/criteria"
}
```

Blocker codes: `geo_restricted`, `stage_floor`, `stage_ceiling`, `revenue_floor`, `entity_type` (e.g. Delaware C-corp only), `nonprofit_only`, `for_profit_only`, `license_required`, `sponsor_bank_required`, `excluded_vertical`, `portfolio_conflict`, `no_cold_inbound`, `cdfi_certification_required`, `affiliation_required`, `closed_program`.

`affiliation_required` covers funders only open to founders with a specific tie — a university, an accelerator alumni network, a demographic eligibility rule, or current student status.

**Preferences are not blockers.** A fund that says it "emphasizes New York State companies" or "mostly sees Southeast Michigan applicants" is stating a preference, not a rule, and must not go in `hard_blockers` — putting it there would wrongly disqualify eligible founders. Preferences belong in `stated_criteria` and feed the match score instead. Only put something in `hard_blockers` if the funder's own words make it a condition of eligibility.

---

## Tier B — your judgment

| Field | Type | Notes |
|---|---|---|
| `decision_timeline_weeks` | int | first contact to money in the bank |
| `reporting_hours_per_quarter` | int | the number nobody publishes |
| `ops_support` | enum | `none`, `light`, `platform_team` |
| `ops_support_detail` | string | what the support actually is, in one line |
| `actively_deploying` | bool | are they writing checks right now |
| `founder_notes` | string | anything a founder should know going in |
| `confidence` | enum | `high`, `medium`, `low`, `unknown` — defaults to `unknown` |

---

## Example record

```json
{
  "funder_id": "fsl",
  "name": "Financial Solutions Lab",
  "url": "https://finhealthnetwork.org",
  "category": "grant_challenge",
  "instruments": ["grant"],
  "stages": ["seed", "series_a"],
  "check_size_min_usd": 100000,
  "check_size_max_usd": 250000,
  "geographies": ["US"],
  "fintech_verticals": ["financial_health", "lending", "wealth"],
  "impact_mandate": "required",
  "impact_reporting_standard": ["custom"],
  "thesis_summary": "Annual challenge backing fintech products that improve financial health for low- and moderate-income households.",
  "stated_criteria": ["..."],
  "hard_blockers": [
    {
      "code": "deadline_based",
      "description": "Applications only open during the annual challenge window",
      "source_quote": "...",
      "source_url": "..."
    }
  ],
  "regulatory_expectation": "none",
  "revenue_required": false,
  "revenue_floor_usd": null,
  "application_mode": "deadline_based",
  "deadlines": [{ "name": "Annual challenge", "date": null, "recurring": true }],
  "application_url": null,
  "decision_timeline_weeks": null,
  "reporting_hours_per_quarter": null,
  "ops_support": null,
  "ops_support_detail": null,
  "actively_deploying": null,
  "founder_notes": null,
  "confidence": "unknown",
  "sources": {
    "check_size_max_usd": {
      "url": "https://...",
      "quote": "each winner received $250,000 in capital",
      "retrieved_at": "2026-10-23"
    }
  },
  "last_verified": "2026-10-23"
}
```

---

## Why these fields

- `hard_blockers` is what turns a list into a tool. It is the field that tells a founder *not* to spend three weeks on a fund.
- `instruments` + `regulatory_expectation` together drive the debt-vs-equity call — a lending startup with a revenue floor met and no license is a different problem from a pre-revenue payments startup.
- `reporting_hours_per_quarter` + `decision_timeline_weeks` + dilution feed the true-cost-of-capital number.
- `sources` doubles as the anti-hallucination guard at runtime: the matcher can only cite funders and claims that exist in the dataset, and the validator rejects anything else.
