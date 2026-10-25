# FinStack

A funding router for US fintech founders. It tells you which money to raise first,
what kind it should be, and why each funder is likely to pass.

Built for MGT 409, AI Foundations for Managers. Author: Ananya Bhattacharya.

---

## Run it

You need **Python 3.11 or newer**. Nothing else to install by hand.

### 1. Put the API key where the app can find it

The app looks for a `.env` file in **two places, in this order**:

1. this repo's own folder
2. the folder one level above the repo

So if the repo sits in `submissions/finstack/`, a `.env` in `submissions/` works
without you doing anything.

The file needs one key:

```
PORTKEY_API_KEY=...
```

See `.env.example`. Every agent runs on `gpt-6-luna` through Portkey. No other key
is needed.

### 2. Set up and start

**Windows (PowerShell or Git Bash):**

```bash
python -m venv venv
venv/Scripts/python.exe -m pip install -r requirements.txt
venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

**macOS / Linux:**

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m uvicorn app.main:app --port 8000
```

### 3. Open it

Go to **http://127.0.0.1:8000**

Click one of the three example buttons at the top (**Balance-sheet lender** is the
most interesting) to fill in all 14 fields at once, then press **Find my capital
stack**. A run takes under a minute and shows each agent as it finishes.

That is the whole setup. If something fails, see Troubleshooting below.

---

## What you get

- An ordered **capital plan** over 12–18 months, not a list of investors
- **Scored matches** with the funder's own words quoted as evidence
- A **skeptic agent** arguing why each top funder would pass on you
- The funders **screened out**, each with the reason
- **Live token usage and cost** for the run, at the bottom of the page

---

## The dataset

`data/funders.json` holds 52 US fintech funders and ships with the repo, so the app
runs immediately with no build step. It is small (about 140 KB) and is the real
dataset, not a sample.

Each funder record has two kinds of fields:

- **Extracted** facts, each carrying the exact sentence from the funder's own page
  that supports it
- **Practitioner** assessments entered by hand in `data/tier_b.csv`, covering things
  no website publishes: whether the fund is currently deploying, reporting burden,
  how long diligence takes

`data/tier_b.csv` is merged on top of the extracted data when the app starts, so you
can edit it and restart without rebuilding anything.

### Rebuilding it (optional, not needed to run the app)

```bash
venv/Scripts/python.exe pipeline/run_build.py --fetch-only    # fetch pages, no API calls
venv/Scripts/python.exe pipeline/run_build.py                 # fetch + extract
venv/Scripts/python.exe pipeline/run_build.py --only qed,i80  # just a couple
```

A full rebuild costs about **$0.03** and writes anything suspicious to
`data/review_queue.csv` for a human to check.

---

## Safety checks

```bash
venv/Scripts/python.exe tests/safety_checks.py
```

Attacks the app on purpose and reports whether each defense held: prompt injection,
invented funders, fabricated numbers, truncated results, runaway spend, key exposure.
Writes the transcript to `data/safety_report.txt`. Add `--offline` to skip the checks
that make real API calls.

---

## Layout

```
app/          the web app: agents, screening, templates
pipeline/     build-time dataset extraction (not needed to run the app)
data/         the funder dataset and the hand-entered assessments
tests/        safety checks, screenshot capture, report and slide builders
report.html   the written report
slides.html   the slide deck
```

---

## Troubleshooting

**`PORTKEY_API_KEY is not set`** — the app checked this folder and the one above it
and found no `.env` with that key. Put the file in either place, then restart.

**Port 8000 already in use** — add `--port 8001` to the uvicorn command and open
http://127.0.0.1:8001 instead.

**`python` not found on Windows** — try `py -3` in place of `python`.

**A run stops with "rejected by the model provider's content filter"** — the
description you entered looked like an instruction to the system rather than a
description of a company. Reword it and try again.
