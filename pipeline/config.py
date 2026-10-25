"""Shared config: key lookup, model, paths.

The API key is read from the environment only. It is never printed, logged, or
written to any output file.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEED_CSV = DATA / "funder_seed_list.csv"
PAGES_DIR = DATA / "pages"
MANUAL_DIR = DATA / "manual"
FUNDERS_JSON = DATA / "funders.json"
REVIEW_CSV = DATA / "review_queue.csv"
USAGE_LOG = DATA / "token_usage.jsonl"

# The assignment allows exactly one model on the course key. Constant on purpose
# so no part of the app can drift to another model.
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# gpt-6-luna rates in USD per 1,000,000 tokens, standard tier.
# Source: https://developers.openai.com/api/docs/pricing (retrieved 2026-10-24).
# Standard applies here: we do not use batch/flex/fast, and a run is far below
# the 272K-token long-context threshold that would move it to the higher tier.
PRICE_PER_1M_INPUT: float | None = 0.10
PRICE_PER_1M_CACHED_INPUT: float | None = 0.01
PRICE_PER_1M_OUTPUT: float | None = 0.50


def rates_set() -> bool:
    return None not in (PRICE_PER_1M_INPUT, PRICE_PER_1M_CACHED_INPUT, PRICE_PER_1M_OUTPUT)


def run_cost_usd(input_tokens: int, cached_tokens: int, output_tokens: int) -> float | None:
    """Cost of one run. Cached input is billed at the cached rate, not the full one."""
    if not rates_set():
        return None
    fresh = max(input_tokens - cached_tokens, 0)
    return (
        fresh / 1_000_000 * PRICE_PER_1M_INPUT
        + cached_tokens / 1_000_000 * PRICE_PER_1M_CACHED_INPUT
        + output_tokens / 1_000_000 * PRICE_PER_1M_OUTPUT
    )

# The assignment's required lookup order: this repo's folder first, then one level up.
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")


def get_client() -> OpenAI:
    """gpt-6-luna through Portkey, via the Responses API."""
    api_key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "PORTKEY_API_KEY is not set. Put it in a .env in this folder "
            "or in the folder one level above."
        )
    return OpenAI(
        api_key=api_key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": api_key},
    )
