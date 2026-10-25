# Founder intake

Intake decides how good every later step can be. A hard blocker can only be
applied if we know the founder's answer, so each question below exists because a
specific blocker code or score input needs it.

## Design

Three layers, in this order:

1. **Structured questions** (below). Dropdowns and short fields. Zero tokens, and
   they give the Python filter everything it needs to run.
2. **Free text**: "Anything else we should know?" plus a paste box for a blurb or
   deck text. Optional.
3. **One intake agent call.** Normalises the answers into the founder profile,
   reads the free text for anything the form missed, and returns up to three
   follow-up questions for fields that are still blank and still matter.

Only step 3 costs tokens, and it runs once.

## The questions

Marked **[filter]** if a hard blocker depends on it — those gate the matching.
Marked **[score]** if it only affects ranking.

| # | Question | Type | Why |
|---|---|---|---|
| 1 | What stage are you? | idea / pre-seed / seed / Series A / later | **[filter]** `stage_floor`, `stage_ceiling` |
| 2 | What does your company do? | free text, 2–3 sentences | **[score]** thesis match |
| 3 | Which best describes your product? | lending, payments, banking infra, embedded finance, insurtech, wealth, regtech, financial health, remittances, SME finance, crypto | **[filter]** `excluded_vertical` |
| 4 | Where are you incorporated, and what entity type? | state + (Delaware C-corp / LLC / PBC / nonprofit / not yet incorporated) | **[filter]** `entity_type`, `nonprofit_only`, `for_profit_only` |
| 5 | Where do you operate? | US states / nationwide / also outside US | **[filter]** `geo_restricted` |
| 6 | Current revenue? | pre-revenue / <$100k / $100k–$500k / $500k–$2M / $2M+ ARR | **[filter]** `revenue_floor` |
| 7 | Licensing and banking status? | none needed / none yet / applications in progress / licensed / sponsor bank secured / chartered | **[filter]** `license_required`, `sponsor_bank_required` |
| 8 | Do you lend money off your own balance sheet? | yes / no / planning to | **[filter]** routes to debt vs equity — the single highest-value question |
| 9 | How much capital, and what for? | amount + (runway / hiring / product / loan book / licensing / marketing) | **[score]** check-size fit, and confirms Q8 |
| 10 | What are you open to? | equity, grants, revenue-based, venture debt, warehouse facility — multi-select | **[filter]** `instruments` |
| 11 | When do you need the money? | <1 month / 1–3 / 3–6 / 6+ months | **[score]** vs `decision_timeline_weeks` |
| 12 | Who does your product serve? | free text + checkboxes: LMI households, thin-file/no-credit, immigrants, small businesses, rural, none specifically | **[filter]** `impact_mandate` eligibility |
| 13 | Besides money, what do you need most? | intros to banks, regulatory help, hiring, distribution, none | **[score]** `ops_support` fit |
| 14 | Any of these apply to the founding team? (optional) | currently a student, underrepresented founder, university affiliation, none / prefer not to say | **[filter]** `affiliation_required` |

## Rules

- **Q14 is optional and unweighted unless answered.** It only ever *adds*
  eligible funders, never removes any. It is never used to score a founder.
- **"I don't know" is a valid answer** on Q6, Q7 and Q11. The profile stores
  `unknown`, and the filter treats an unknown as "do not disqualify" — it keeps
  the funder in and labels the match `needs confirmation` instead of guessing.
- **Nothing is inferred silently.** If the agent derives a field from free text
  rather than a direct answer, the profile marks it `inferred` and the UI shows
  it back to the founder for correction.

## Follow-ups

After the agent call, if a **[filter]** field is still blank, the UI says which
funders cannot be screened without it, e.g.:

> We can't check 11 debt funders without knowing whether you lend off your own
> balance sheet. Answer Q8 to include them.

That keeps the cost of a blank field visible instead of silently narrowing the
results.
