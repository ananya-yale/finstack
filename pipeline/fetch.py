"""Fetch funder pages and cache them as plain text.

Build-time only. Nothing here calls an LLM, so this step costs zero tokens.

For each funder we fetch the main URL, then follow up to MAX_SUBPAGES internal
links whose anchor text looks like eligibility or thesis material. The cached
text is what the extractor reads, so quotes in the dataset can always be traced
back to a real page.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from io import BytesIO
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from config import MANUAL_DIR, PAGES_DIR

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 20.0
MAX_SUBPAGES = 3
MAX_CHARS = 14_000  # cap per funder; keeps the extraction prompt bounded

# Anchor text worth following. Ordered: earlier patterns win when we can only take a few.
LINK_HINTS = [
    r"\b(criteria|eligib|qualif|who (we|can) (fund|back|apply))\b",
    r"\b(how to apply|apply|application|submit|pitch|guidelines)\b",
    r"\b(technical assistance|awards?|funding opportunit|notice of funding)\b",
    r"\b(thesis|investment approach|how we invest|focus)\b",
    r"\b(about|overview|our work|faq)\b",
    r"\b(grant|program|fund)\b",
]

SKIP_EXT = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip", ".mp4", ".webp", ".css", ".js")


@dataclass
class FetchResult:
    funder_id: str
    url: str
    ok: bool
    text: str = ""
    pages: list[str] = field(default_factory=list)
    error: str = ""


SMART_CHARS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", " ": " ",
}


def _normalise_text(text: str) -> str:
    """Flatten smart punctuation so quotes survive the round trip into JSON."""
    for bad, good in SMART_CHARS.items():
        text = text.replace(bad, good)
    return text


def _clean(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    return _normalise_text(re.sub(r"\n{3,}", "\n\n", text))


def _pdf_text(raw: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(raw))
    return "\n".join((page.extract_text() or "") for page in reader.pages[:10])


def _get(client: httpx.Client, url: str) -> tuple[str, str]:
    """Return (text, content_type). Raises on HTTP error."""
    resp = client.get(url)
    resp.raise_for_status()
    ctype = resp.headers.get("content-type", "")
    if "pdf" in ctype.lower() or url.lower().endswith(".pdf"):
        return _pdf_text(resp.content), "pdf"
    return _clean(resp.text), "html"


def _candidate_links(html: str, base_url: str) -> list[str]:
    """Internal links whose anchor text suggests eligibility or thesis content."""
    soup = BeautifulSoup(html, "html.parser")
    host = urlparse(base_url).netloc
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        label = a.get_text(" ", strip=True).lower()
        if not label or len(label) > 60:
            continue
        href = urljoin(base_url, a["href"]).split("#")[0]
        if href in seen or urlparse(href).netloc != host:
            continue
        if href.lower().endswith(SKIP_EXT):
            continue
        for rank, pattern in enumerate(LINK_HINTS):
            if re.search(pattern, label):
                seen.add(href)
                scored.append((rank, href))
                break

    scored.sort(key=lambda pair: pair[0])
    return [href for _, href in scored]


def fetch_funder(funder_id: str, url: str) -> FetchResult:
    """Fetch one funder's pages. Cached to data/pages/<funder_id>.txt."""
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Manual override: some sites block automated clients (403) or render only in
    # the browser. For those, paste the page text into data/manual/<id>.txt by hand
    # and the pipeline uses it as the source, so quotes stay traceable.
    manual = MANUAL_DIR / f"{funder_id}.txt"
    if manual.exists():
        text = _normalise_text(manual.read_text(encoding="utf-8"))[:MAX_CHARS]
        return FetchResult(funder_id, url, True, text, [f"{url} (manual paste)"])

    cache = PAGES_DIR / f"{funder_id}.txt"
    if cache.exists():
        payload = json.loads(cache.read_text(encoding="utf-8"))
        return FetchResult(funder_id, url, True, payload["text"], payload["pages"])

    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    try:
        with httpx.Client(
            follow_redirects=True, timeout=TIMEOUT, headers=headers, verify=True
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            if not resp.charset_encoding:
                resp.default_encoding = "utf-8"
            raw_html = resp.text
            main = _clean(raw_html)
            pages = [str(resp.url)]
            chunks = [f"=== SOURCE: {resp.url} ===\n{main}"]

            for link in _candidate_links(raw_html, str(resp.url))[:MAX_SUBPAGES]:
                try:
                    text, _ = _get(client, link)
                except Exception:
                    continue
                if len(text) > 200:
                    pages.append(link)
                    chunks.append(f"=== SOURCE: {link} ===\n{text}")

        combined = "\n\n".join(chunks)[:MAX_CHARS]
        if len(combined.strip()) < 200:
            return FetchResult(funder_id, url, False, error="page had almost no text (likely JS-rendered)")

        cache.write_text(
            json.dumps({"url": url, "pages": pages, "text": combined}), encoding="utf-8"
        )
        return FetchResult(funder_id, url, True, combined, pages)

    except httpx.HTTPStatusError as exc:
        return FetchResult(funder_id, url, False, error=f"HTTP {exc.response.status_code}")
    except Exception as exc:  # noqa: BLE001 - we want the reason in the review queue
        return FetchResult(funder_id, url, False, error=f"{type(exc).__name__}: {exc}")
