"""FinStack - web app.

    python -m uvicorn app.main:app   (from the repo root)

One run = four model calls: intake, match, plan, skeptic. Everything before the
matcher is plain Python, so the dataset can grow without the cost growing.

A run takes most of a minute, so POST /match starts it on a background thread and
returns a progress page straight away. That page polls /api/job/<id> and shows each
agent as it finishes, then loads the result. The stages reported are the real ones -
nothing is advanced on a timer.
"""

from __future__ import annotations

import sys
import threading
import traceback
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR.parent / "pipeline"))

from agents import (  # noqa: E402
    SHORTLIST_SIZE, Usage, run_intake, run_match, run_plan, run_skeptic,
)
from config import run_cost_usd  # noqa: E402
from screen import prerank, screen_all  # noqa: E402
from store import coverage, load_funders  # noqa: E402

app = FastAPI(title="FinStack")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
(APP_DIR / "static").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

FUNDERS = load_funders()
COVERAGE = coverage(FUNDERS)

# Runs in flight, keyed by job id. Single process, so a plain dict is enough.
JOBS: dict[str, dict] = {}

STAGES = [
    ("intake", "Reading your profile", "intake agent"),
    ("screen", f"Screening {len(FUNDERS)} funders", "no model call"),
    ("match", "Scoring the shortlist", "matcher agent"),
    ("plan", "Sequencing your capital stack", "planner agent"),
    ("skeptic", "Stress-testing the top matches", "skeptic agent"),
]


def _multi(raw: str | None) -> list[str]:
    return [v for v in (raw or "").split(",") if v]


def _run_pipeline(job_id: str, form: dict, free_text: str) -> None:
    job = JOBS[job_id]
    usage = Usage()
    try:
        job["stage"] = "intake"
        intake, injection_flags = run_intake(usage, form, free_text)
        profile = intake.profile
        job["done"].append("intake")

        job["stage"] = "screen"
        eligible, excluded = screen_all(FUNDERS, profile)
        shortlist_items = prerank(eligible, profile, SHORTLIST_SIZE)
        shortlist = [item.funder for item in shortlist_items]
        screened_by_id = {item.funder["funder_id"]: item for item in shortlist_items}
        job["done"].append("screen")
        job["screen_note"] = (
            f"{len(FUNDERS)} to {len(eligible)} eligible to {len(shortlist)} shortlisted"
        )

        job["stage"] = "match"
        matches, skipped = run_match(usage, profile, shortlist)
        job["done"].append("match")

        job["stage"] = "plan"
        plan = run_plan(usage, profile, matches, shortlist)
        job["done"].append("plan")

        job["stage"] = "skeptic"
        objections = run_skeptic(usage, profile, matches, shortlist)
        job["done"].append("skeptic")

        by_id = {f["funder_id"]: f for f in FUNDERS}
        cards = [
            {
                "match": m,
                "funder": by_id[m.funder_id],
                "screened": screened_by_id.get(m.funder_id),
                "objection": next((o for o in objections if o.funder_id == m.funder_id), None),
            }
            for m in matches if m.funder_id in by_id
        ]

        used = usage.as_dict()
        job["context"] = {
            "profile": profile, "cards": cards, "plan": plan,
            "names": {f["funder_id"]: f["name"] for f in shortlist},
            "follow_ups": intake.follow_ups, "injection_flags": injection_flags,
            "usage": used, "coverage": COVERAGE, "skipped": skipped,
            "cost": run_cost_usd(
                used["input_tokens"], used["cached_input_tokens"], used["output_tokens"]
            ),
            "counts": {
                "total": len(FUNDERS), "eligible": len(eligible),
                "excluded": len(excluded), "shortlisted": len(shortlist),
            },
            "excluded": [
                {"name": e.funder["name"], "why": e.excluded_by[0] if e.excluded_by else ""}
                for e in excluded
            ][:12],
        }
        job["status"] = "done"

    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        job["status"] = "error"
        job["error"] = str(exc)
        job["usage"] = usage.as_dict()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "form.html", {"coverage": COVERAGE})


@app.post("/match", response_class=HTMLResponse)
def match(
    request: Request,
    stage: str = Form(...),
    description: str = Form(""),
    vertical: str = Form(...),
    entity_type: str = Form("unknown"),
    incorporation_state: str = Form(""),
    operating_geographies: str = Form(""),
    revenue: str = Form("unknown"),
    regulatory_status: str = Form("unknown"),
    lends_own_balance_sheet: str = Form("unknown"),
    capital_sought_usd: str = Form(""),
    use_of_funds: str = Form(""),
    open_to_instruments: str = Form(""),
    timeline: str = Form("unknown"),
    populations_served: str = Form(""),
    support_needed: str = Form(""),
    founder_attributes: str = Form(""),
    free_text: str = Form(""),
):
    form = {
        "stage": stage, "description": description[:600], "vertical": vertical,
        "entity_type": entity_type, "incorporation_state": incorporation_state or None,
        "operating_geographies": _multi(operating_geographies),
        "revenue": revenue, "regulatory_status": regulatory_status,
        "lends_own_balance_sheet": lends_own_balance_sheet,
        "capital_sought_usd": int(capital_sought_usd) if capital_sought_usd.isdigit() else None,
        "use_of_funds": _multi(use_of_funds),
        "open_to_instruments": _multi(open_to_instruments),
        "timeline": timeline,
        "populations_served": _multi(populations_served),
        "support_needed": _multi(support_needed),
        "founder_attributes": _multi(founder_attributes),
    }

    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {"status": "running", "stage": "intake", "done": [], "screen_note": ""}
    threading.Thread(target=_run_pipeline, args=(job_id, form, free_text), daemon=True).start()

    return templates.TemplateResponse(
        request, "progress.html", {"job_id": job_id, "stages": STAGES}
    )


@app.get("/api/job/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return JSONResponse({"status": "missing"}, status_code=404)
    return JSONResponse({
        "status": job["status"],
        "stage": job.get("stage"),
        "done": job["done"],
        "screen_note": job.get("screen_note", ""),
        "error": job.get("error", ""),
    })


@app.get("/results/{job_id}", response_class=HTMLResponse)
def results(request: Request, job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return templates.TemplateResponse(
            request, "error.html",
            {"message": "That result has expired. Please run it again.",
             "usage": {"input_tokens": 0, "output_tokens": 0, "calls": 0}},
            status_code=404,
        )
    if job["status"] == "error":
        return templates.TemplateResponse(
            request, "error.html",
            {"message": job["error"], "usage": job.get("usage", {})},
            status_code=500,
        )
    if job["status"] != "done":
        return templates.TemplateResponse(
            request, "progress.html", {"job_id": job_id, "stages": STAGES}
        )
    return templates.TemplateResponse(request, "results.html", job["context"])
