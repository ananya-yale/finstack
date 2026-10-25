"""Build slides.html: a 10-slide reveal.js deck, self-contained apart from the CDN.

    ../venv/Scripts/python.exe tests/build_slides.py

reveal.js comes from a CDN (as the assignment specifies). Every image is
base64-embedded, so the file still works when emailed.
"""

from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "report_assets"
OUT = ROOT / "slides.html"

REVEAL = "https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist"


def data_uri(name: str) -> str:
    path = next(ASSETS.glob(f"{name}.*"))
    mime = "image/svg+xml" if path.suffix == ".svg" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


SLIDES = f"""
<!-- 1 ............................................................. title -->
<section data-background-color="#13262F" class="title-slide">
  <div class="mark">
    <svg viewBox="0 0 24 24" width="70" height="70">
      <rect x="1.5" y="17" width="21" height="4.4" rx="1.4" fill="#90A583"/>
      <rect x="5" y="11.1" width="14" height="4.4" rx="1.4" fill="#C2A3A4"/>
      <g transform="rotate(-9 12 6)">
        <rect x="6.3" y="2.9" width="11.4" height="6.2" rx="1.2" fill="#FAF7F5"/>
        <circle cx="12" cy="6" r="1.65" fill="#13262F"/>
      </g>
    </svg>
  </div>
  <h1>Fin<span class="sage">Stack</span></h1>
  <p class="for-who">For fintech founders</p>
  <p class="pitch">Which money to raise first, what kind it should be,<br>
  and why each funder is likely to pass.</p>
  <p class="byline">Ananya Bhattacharya &middot; MGT 409 Final Project</p>
</section>

<!-- 2 ........................................................... problem -->
<section>
  <h2>Founders can find investor lists. That is not the problem.</h2>
  <p class="blockers">The blockers are:</p>
  <div class="three">
    <div><span class="num">1</span>
      <h3>Am I even eligible?</h3>
      <p>Funds rarely publish what rules you out. You find out after the
      rejection.</p></div>
    <div><span class="num">2</span>
      <h3>Do I need equity at all?</h3>
      <p>Lending off your balance sheet? You need a warehouse facility, from an
      entirely different set of people.</p></div>
    <div><span class="num">3</span>
      <h3>What does it really cost?</h3>
      <p>Everyone compares dilution. Nobody compares reporting hours or whether
      the fund is even deploying.</p></div>
  </div>
  <p class="kicker">Today you get these answers by knowing someone.</p>
</section>

<!-- 3 ......................................................... what is new -->
<section>
  <h2>What FinStack provides that others don't</h2>
  <div class="two">
    <div>
      <ul class="big">
        <li><strong>An order, not a list.</strong> A plan over 12&ndash;18 months
          where each step says what it unlocks.</li>
        <li><strong>It knows when you need debt, not equity.</strong> If you lend off
          your own balance sheet, a bigger equity round is the wrong answer. You need a
          warehouse facility from a specialty credit fund. Raising equity instead means
          giving away ownership to fund loans.</li>
        <li><strong>It stress-tests your pitch.</strong> One agent argues the case
          against you, so you see the gaps a funder would raise before they raise
          them.</li>
      </ul>
    </div>
    <div class="evidence">
      <p class="ev-head">Why simple scraping is not enough</p>
      <table>
        <tr><td class="n">26<span>/52</span></td><td>funders publish their stage</td></tr>
        <tr><td class="n">19<span>/52</span></td><td>publish check sizes</td></tr>
        <tr><td class="n">0<span>/52</span></td><td>publish licensing expectations</td></tr>
        <tr><td class="n sage">8</td><td>are not deploying right now, and no
          website says so</td></tr>
      </table>
      <p class="ev-foot">Compared against OpenVC, Signal by NFX, Crunchbase,
      Foundersuite, Instrumentl and ChatGPT with search.</p>
    </div>
  </div>
</section>

<!-- 4 ........................................................ architecture -->
<section>
  <h2>How it works: 5 agents, 4 model calls</h2>
  <img class="diagram" src="{data_uri('architecture')}" alt="Architecture diagram">
</section>

<!-- 5 ................................................................ demo -->
<section>
  <h2>Example: Seed lending startup raising $2M</h2>
  <div class="two demo">
    <div><img src="{data_uri('05_plan')}" alt="The capital plan"></div>
    <div>
      <p class="lead">The plan put <span class="sage">equity last</span>.</p>
      <ol class="steps">
        <li>Get the regulatory package together</li>
        <li><strong>i80 Group</strong> &rarr; warehouse facility for the loan book</li>
        <li><strong>Victory Park</strong> &rarr; second facility conversation</li>
        <li><strong>Zeal Capital</strong> &rarr; equity, once there is lending traction</li>
      </ol>
      <p class="note">A generic tool would have sent them to raise equity first.</p>
    </div>
  </div>
</section>

<!-- 6 ........................................................ skeptic agent -->
<section>
  <h2>FinStack tells you where your pitch may fall short</h2>
  <img class="card" src="{data_uri('06_match_card')}" alt="A match card with the skeptic's objection">
</section>

<!-- 7 ................................................................ cost -->
<section>
  <h2>What it costs to run</h2>
  <div class="stats">
    <div><span class="stat">$0.0032</span><span class="lab">one founder, one run</span></div>
    <div><span class="stat">$0.96</span><span class="lab">100 founders / month</span></div>
    <div><span class="stat">$96</span><span class="lab">10,000 founders / month</span></div>
    <div><span class="stat">$0.03</span><span class="lab">to build the whole dataset</span></div>
  </div>
  <div class="two cost-why">
    <div>
      <p class="lead">Why it stays cheap</p>
      <ul>
        <li>Eligibility filtering is ordinary code, not AI: <strong>52 &rarr; 31 &rarr;
          25</strong> before any model call. Saves ~30% per run.</li>
        <li>One batched call scores all 25 funders, not 25 separate calls.</li>
        <li>The skeptic only looks at the top 3.</li>
      </ul>
    </div>
    <div><img src="{data_uri('08_cost')}" alt="Token usage panel"></div>
  </div>
</section>

<!-- 8 .............................................................. safety -->
<section>
  <h2>Safety: two defenses, both tested</h2>
  <div class="two">
    <div class="def">
      <p class="ev-head">It caught a made-up number</p>
      <p>The extractor claimed QED writes $3M&ndash;$10M checks and attached a real
      quote about <strong>$15M</strong> to prove it.</p>
      <p>Numbers are only kept if they appear in their own quote. All three
      invented check sizes were dropped before anyone saw them.</p>
    </div>
    <div class="def">
      <p class="ev-head">It survived a deliberate attack</p>
      <p>I typed a fake "note from the platform operator" into the description,
      demanding one fund be scored 100 and <strong>only that result returned</strong>.</p>
      <p class="result">It asked for 1 result.<br><span class="sage">It got 25.</span></p>
      <p class="small">The fund it named had already been filtered out as
      student-founders-only.</p>
    </div>
  </div>
  <p class="kicker">7 of 7 safety checks passing. Testing also found a real bug:
  an injection used to cut results from 25 to 8 with nothing on screen to say so.</p>
</section>

<!-- 9 ............................................................. impact -->
<section>
  <h2>Impact</h2>
  <div class="two">
    <div>
      <ul class="big">
        <li><strong>~1 week of founder time saved.</strong> Eight funders in the
          dataset are not deploying. Every one has a polished website, so a scraper
          or ChatGPT recommends all eight.</li>
        <li><strong>Points of dilution.</strong> A balance-sheet lender who raises
          equity instead of a facility gives away ownership to fund loan assets.</li>
      </ul>
    </div>
    <div class="quote">
      <p>Funds keep private databases of peer investors and what they require, plus
      call notes from fund-to-fund conversations. None of it is public. Founders only
      get this by building relationships, which is hardest when you are early or a
      first-time founder.</p>
      <p class="attrib">Practitioner review &mdash; venture philanthropy investing in
      economic mobility ventures</p>
    </div>
  </div>
</section>

<!-- 10 ............................................................... next -->
<section data-background-color="#13262F" class="end-slide">
  <h2 class="light">What is next</h2>
  <div class="two">
    <div>
      <ul class="big light">
        <li>A true <strong>cost of capital</strong> number: dilution plus reporting
          hours plus diligence time.</li>
        <li>An <strong>investor-side mode</strong> that turns a rejection into a
          referral.</li>
        <li><strong>Monthly re-verification</strong>. It costs three cents.</li>
      </ul>
    </div>
    <div>
      <p class="limit-head">The honest limit</p>
      <p class="limit">Some funders are vague about their thesis on purpose, so this
      needs constant updating. And the most valuable things I know come from my
      network, which raises a real question about how much of it I should publish.</p>
    </div>
  </div>
</section>
"""

CSS = """
  :root{
    --navy:#13262F; --sage:#90A583; --mauve:#7A6263; --mauve-deep:#5E4A4B;
    --paper:#FAF7F5; --line:#E6DEDB; --muted:#6E6668; --mauve-soft:#F4EBEA;
  }
  .reveal{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    font-size:34px; color:var(--navy);
  }
  html,body,.reveal-viewport,.reveal{background:var(--paper)}
  .reveal .slides{text-align:left}

  .reveal h1,.reveal h2,.reveal h3{
    font-family:inherit; text-transform:none; letter-spacing:-.02em; color:var(--navy);
    font-weight:800; margin:0;
  }
  .reveal h2{
    font-size:1.5em; line-height:1.15; margin:0 0 .55em;
    padding-bottom:.3em; border-bottom:3px solid var(--mauve-soft);
  }
  .reveal h2.light{color:var(--paper); border-bottom-color:rgba(255,255,255,.18)}
  .reveal p{line-height:1.45; margin:0 0 .6em}
  .reveal strong{color:var(--mauve-deep)}
  .sage{color:var(--sage)}
  .reveal .small{font-size:.72em; color:var(--muted)}

  /* title */
  .title-slide .mark{margin-bottom:.35em}
  .reveal .title-slide h1{font-size:3.4em; color:#fff; letter-spacing:-.035em}
  .reveal .title-slide .for-who{font-size:.62em; letter-spacing:.2em;
    text-transform:uppercase; color:var(--sage); font-weight:800; margin:.5em 0 .3em}
  .reveal .title-slide .pitch{font-size:1.15em; color:#DED5D3; margin:0 0 1.1em;
    line-height:1.35}
  .reveal .title-slide .byline{font-size:.72em; color:var(--sage); letter-spacing:.12em;
    text-transform:uppercase; font-weight:700; margin:0}

  /* layout helpers */
  .two{display:grid; grid-template-columns:1fr 1fr; gap:1.3em; align-items:start}
  .reveal .blockers{font-size:.82em; font-weight:800; color:var(--mauve-deep);
    margin:-.25em 0 .6em}
  .three{display:grid; grid-template-columns:repeat(3,1fr); gap:1.1em; margin-bottom:.8em}
  .three .num{display:inline-flex; width:1.5em; height:1.5em; border-radius:50%;
    background:var(--mauve); color:#fff; align-items:center; justify-content:center;
    font-weight:800; font-size:.8em; margin-bottom:.35em}
  .reveal .three h3{font-size:.92em; margin:0 0 .25em}
  .reveal .three p{font-size:.76em; color:var(--muted); margin:0}
  .reveal .kicker{font-size:.8em; color:var(--mauve); font-weight:700; margin:.5em 0 0;
    padding-top:.5em; border-top:2px solid var(--mauve-soft)}

  .reveal ul.big{list-style:none; margin:0; padding:0}
  .reveal ul.big li{margin:0 0 .7em; padding-left:1em; position:relative;
    font-size:.86em; line-height:1.4}
  .reveal ul.big li:before{content:""; position:absolute; left:0; top:.5em;
    width:.42em; height:.42em; border-radius:50%; background:var(--sage)}
  .reveal ul.big.light li{color:#E6E0DE}
  .reveal ul.big.light strong{color:var(--sage)}

  /* evidence panel */
  .evidence{background:#fff; border:1px solid var(--line); border-top:4px solid var(--mauve);
    border-radius:4px; padding:.8em .9em}
  .ev-head{font-size:.62em !important; letter-spacing:.14em; text-transform:uppercase;
    color:var(--mauve); font-weight:800; margin:0 0 .5em !important}
  .evidence table{width:100%; font-size:.76em; border-collapse:collapse}
  .evidence td{padding:.22em 0; vertical-align:baseline; border:0}
  .evidence td.n{font-weight:800; font-size:1.25em; color:var(--mauve);
    width:2.6em; letter-spacing:-.02em}
  .evidence td.n.sage{color:#4e7a3a}
  .evidence td.n span{font-size:.55em; font-weight:600; color:var(--muted)}
  .ev-foot{font-size:.6em !important; color:var(--muted); margin:.6em 0 0 !important;
    line-height:1.3}

  /* images */
  .reveal img{border:1px solid var(--line); border-radius:4px; display:block;
    margin:0; max-width:100%}
  .reveal img.diagram{border:0; width:100%; margin:0 auto; max-height:76vh;
    object-fit:contain}
  .reveal img.card{width:76%; margin:0 auto; max-height:70vh; object-fit:contain;
    object-position:top}
  .demo{grid-template-columns:1.25fr 1fr}
  .demo img{max-height:74vh; width:100%; object-fit:contain; object-position:top}

  .reveal .lead{font-weight:800; font-size:1.0em; margin:0 0 .4em}
  .reveal ol.steps{margin:0 0 .6em; padding-left:1.1em; font-size:.8em}
  .reveal ol.steps li{margin:.3em 0; line-height:1.35}
  .reveal .note{font-size:.72em; color:var(--muted); font-style:italic}

  /* stats row */
  .stats{display:grid; grid-template-columns:repeat(4,1fr); gap:.8em; margin-bottom:.9em}
  .stats > div{background:#fff; border:1px solid var(--line); border-top:4px solid var(--sage);
    border-radius:4px; padding:.6em .7em}
  .stat{display:block; font-size:1.45em; font-weight:800; color:var(--mauve);
    letter-spacing:-.03em; line-height:1}
  .lab{display:block; font-size:.6em; color:var(--muted); margin-top:.3em; line-height:1.25}
  .cost-why ul{margin:0; padding-left:1em; font-size:.74em}
  .cost-why li{margin:.35em 0; line-height:1.35}
  .cost-why img{max-height:34vh; object-fit:contain; object-position:top}

  /* safety */
  .def{background:#fff; border:1px solid var(--line); border-top:4px solid var(--mauve);
    border-radius:4px; padding:.85em .95em}
  .def p{font-size:.78em; line-height:1.4}
  .reveal .def .result{font-size:1.15em; font-weight:800; margin:.5em 0 .3em;
    line-height:1.25}

  /* impact quote */
  .quote{background:var(--mauve); color:#fff; border-radius:4px; padding:1em 1.1em}
  .reveal .quote p{font-size:.8em; line-height:1.45; color:#fff}
  .reveal .quote .attrib{font-size:.62em; color:#E2D3D3; margin:.6em 0 0; font-style:italic}

  /* end slide */
  .end-slide .limit-head{font-size:.62em !important; letter-spacing:.14em;
    text-transform:uppercase; color:var(--sage); font-weight:800; margin:0 0 .5em !important}
  .reveal .end-slide .limit{font-size:.8em; color:#D8D1CF; line-height:1.45;
    border-left:3px solid var(--sage); padding-left:.8em}

  /* sits outside .slides so it shows on every slide, including the dark ones */
  .deck-logo{position:fixed; left:26px; bottom:20px; z-index:40;
    display:flex; align-items:center; gap:8px; pointer-events:none;
    background:rgba(255,255,255,.72); border:1px solid rgba(19,38,47,.10);
    border-radius:999px; padding:5px 13px 5px 6px;
    -webkit-backdrop-filter:blur(3px); backdrop-filter:blur(3px)}
  .deck-logo span{font-size:15px; font-weight:800; letter-spacing:-.02em;
    color:var(--navy); line-height:1}
  .deck-logo span .sage{color:#4e7a3a}
  .reveal .progress{color:var(--mauve)}
  .reveal .slide-number{background:transparent; color:var(--muted); font-size:.5em}
"""

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FinStack &mdash; MGT 409 Final Project</title>
<link rel="stylesheet" href="{REVEAL}/reveal.css">
<style>{CSS}</style>
</head>
<body>
<div class="reveal">
<div class="deck-logo" aria-hidden="true">
  <svg viewBox="0 0 24 24" width="26" height="26">
    <rect width="24" height="24" rx="5" fill="#13262F"/>
    <rect x="2.6" y="16.6" width="18.8" height="4.1" rx="1.3" fill="#90A583"/>
    <rect x="5.5" y="11" width="13" height="4.1" rx="1.3" fill="#C2A3A4"/>
    <g transform="rotate(-9 12 6.2)">
      <rect x="6.4" y="3.2" width="11.2" height="5.9" rx="1.2" fill="#FAF7F5"/>
      <circle cx="12" cy="6.2" r="1.6" fill="#13262F"/>
    </g>
  </svg>
  <span>Fin<span class="sage">Stack</span></span>
</div>
<div class="slides">
{SLIDES}
</div></div>
<script src="{REVEAL}/reveal.js"></script>
<script>
  Reveal.initialize({{
    width: 1280, height: 720, margin: 0.055, center: true,
    minScale: 0.2, maxScale: 1.6,
    hash: true, slideNumber: 'c/t', transition: 'fade', controls: true, progress: true
  }});
</script>
</body>
</html>"""

OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT.name}  ({OUT.stat().st_size // 1024:,} KB, "
      f"{HTML.count('<section')} slides)")
