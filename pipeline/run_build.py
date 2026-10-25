"""Build data/funders.json from data/funder_seed_list.csv.

    python pipeline/run_build.py --only btv,qed     # smoke test a few
    python pipeline/run_build.py --limit 5
    python pipeline/run_build.py                    # everything marked keep=y

Fetching is cached, so re-running only re-extracts. Anything that fails to fetch
or produces an unsupported quote lands in data/review_queue.csv for a human.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import FUNDERS_JSON, REVIEW_CSV, SEED_CSV  # noqa: E402
from extract import extract_funder  # noqa: E402
from fetch import fetch_funder  # noqa: E402


def load_seed() -> list[dict]:
    with SEED_CSV.open(encoding="utf-8-sig", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r.get("id")]
    return [r for r in rows if (r.get("keep") or "").strip().lower() == "y"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="comma-separated funder ids")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--fetch-only", action="store_true", help="no LLM calls")
    args = parser.parse_args()

    seed = load_seed()
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        seed = [r for r in seed if r["id"] in wanted]
    if args.limit:
        seed = seed[: args.limit]

    records: list[dict] = []
    review: list[dict] = []
    totals = {"input": 0, "cached": 0, "output": 0}

    for i, row in enumerate(seed, 1):
        fid, name, url = row["id"], row["name"], row["url"]
        print(f"[{i}/{len(seed)}] {fid} ... ", end="", flush=True)

        fetched = fetch_funder(fid, url)
        if not fetched.ok:
            print(f"FETCH FAILED ({fetched.error})")
            review.append({"funder_id": fid, "name": name, "url": url,
                           "issue": "fetch_failed", "detail": fetched.error})
            continue

        if args.fetch_only:
            print(f"fetched {len(fetched.text)} chars from {len(fetched.pages)} page(s)")
            continue

        try:
            record = extract_funder(fid, name, fetched.text, fetched.pages)
        except Exception as exc:  # noqa: BLE001
            print(f"EXTRACT FAILED ({type(exc).__name__}: {exc})")
            review.append({"funder_id": fid, "name": name, "url": url,
                           "issue": "extract_failed", "detail": str(exc)[:200]})
            continue

        usage = record.pop("usage")
        totals["input"] += usage["input_tokens"]
        totals["cached"] += usage["cached_input_tokens"]
        totals["output"] += usage["output_tokens"]

        if not record["page_supports_extraction"]:
            review.append({"funder_id": fid, "name": name, "url": url,
                           "issue": "page_not_usable", "detail": "model says page lacks criteria"})
        for dropped in record["dropped_unsupported"]:
            review.append({"funder_id": fid, "name": name, "url": url,
                           "issue": "unsupported_quote", "detail": dropped})

        records.append(record)
        flag = " [REVIEW]" if record["dropped_unsupported"] else ""
        print(
            f"ok  blockers={len(record['hard_blockers'])} "
            f"criteria={len(record['stated_criteria'])} "
            f"tokens in={usage['input_tokens']} cached={usage['cached_input_tokens']} "
            f"out={usage['output_tokens']}{flag}"
        )

    if args.fetch_only:
        return

    if records:
        existing = {}
        if FUNDERS_JSON.exists():
            existing = {r["funder_id"]: r for r in json.loads(FUNDERS_JSON.read_text("utf-8"))}
        for record in records:
            existing[record["funder_id"]] = record
        FUNDERS_JSON.write_text(
            json.dumps(list(existing.values()), indent=2), encoding="utf-8"
        )

    with REVIEW_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["funder_id", "name", "url", "issue", "detail"])
        writer.writeheader()
        writer.writerows(review)

    print(
        f"\n{len(records)} extracted, {len(review)} review items -> {REVIEW_CSV.name}\n"
        f"tokens: input={totals['input']} cached={totals['cached']} output={totals['output']}"
    )


if __name__ == "__main__":
    main()
