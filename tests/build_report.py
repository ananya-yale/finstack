"""Build report.html as a single self-contained file.

    ../venv/Scripts/python.exe tests/build_report.py

Every image in report_assets/ is base64-embedded, so the file opens by
double-clicking on any computer with nothing missing.
"""

from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "report_assets"
OUT = ROOT / "report.html"


def img(name: str, caption: str, width: str = "100%") -> str:
    path = next(ASSETS.glob(f"{name}.*"))
    mime = "image/svg+xml" if path.suffix == ".svg" else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode()
    return (f'<figure><img src="data:{mime};base64,{data}" alt="{caption}" '
            f'style="width:{width}">'
            f'<figcaption>{caption}</figcaption></figure>')


def code(text: str) -> str:
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<pre>{safe}</pre>"


BODY = f"""
<header class="cover">
  <p class="eyebrow">MGT 409 &middot; AI Foundations for Managers &middot; Final Project</p>
  <h1>FinStack</h1>
  <p class="sub">A funding router for US fintech founders. It tells you which money to
  raise first, what kind it should be, and why each funder is likely to pass.</p>
  <table class="meta">
    <tr><td>Author</td><td>Ananya Bhattacharya</td></tr>
    <tr><td>Repository</td><td><a href="https://github.com/ananya-yale/finstack">github.com/ananya-yale/finstack</a></td></tr>
    <tr><td>Running the app</td><td>Locally from a fresh clone. See <code>README.md</code>.</td></tr>
    <tr><td>Model</td><td>gpt-6-luna via Portkey, for every agent</td></tr>
    <tr><td>Date</td><td>October 2026</td></tr>
  </table>
</header>

<h2>2. Motivation</h2>

<p>I have spent time on the investor side of early-stage fintech, and the thing that
strikes me every time is how much founder effort gets burned on conversations that were
never going to end in a check. It is rarely because the founder is weak or because they
could not find investors, since investor lists are everywhere and mostly free.</p>

<p>The waste comes from three things a list cannot tell you.</p>

<p><strong>Whether you are even eligible.</strong> Funds rarely publish the things that
rule you out. A fund that only writes Series A checks. A grant that requires you to be a
certified CDFI. A program that only backs student founders. All of this is knowable, but
it is buried, and most founders find out after the rejection rather than before the
pitch.</p>

<p><strong>Whether you need equity at all.</strong> This is the one that costs real
money, and it is specific to fintech. If you are lending off your own balance sheet, you
do not need a bigger seed round to fund your loan book. You need a warehouse facility,
and that comes from an entirely different set of people: specialty credit funds rather
than venture funds. Founders raise dilutive equity to fund loan assets all the time. It is
one of the most expensive mistakes in the sector and it usually comes down to not knowing
the debt market is there.</p>

<p><strong>What the money actually costs you.</strong> Everyone compares dilution.
Almost nobody compares how many hours a quarter you will spend on reporting, how long
diligence takes, or whether the fund is even writing checks right now. A grant with
thirty hours of quarterly reporting can be more expensive for a three-person team than
giving up a few points.</p>

<p>Right now a founder gets these answers by asking someone who already knows, which
makes the quality of the answer depend on who they happen to know. That is the part of
venture hardest to break into from the outside. I wanted to see whether I could put what
people like me know into something a founder could use without an introduction first.</p>

<h2>3. What is new here</h2>

<p>I looked at what already exists before I built anything. The closest comparisons:</p>

<table class="compare">
  <tr><th>Product</th><th>What it does</th><th>What it does not do</th></tr>
  <tr><td><strong>OpenVC</strong></td><td>Free investor database you can filter by
    stage and sector</td><td>Gives you a filtered list, not an order of operations. No
    debt providers, and no view on who is actually deploying</td></tr>
  <tr><td><strong>Signal by NFX</strong></td><td>Investor search, built around finding a
    warm intro</td><td>Equity only, and it works best if you already have a network.
    That is the thing an outsider does not have</td></tr>
  <tr><td><strong>Crunchbase / PitchBook</strong></td><td>Deep data on companies and
    investors</td><td>Tells you what happened, not what you qualify for. Priced for
    institutions, not pre-seed founders</td></tr>
  <tr><td><strong>Visible Connect, Foundersuite</strong></td><td>Investor directories
    and fundraising CRM</td><td>Help you run a process you have already decided on</td></tr>
  <tr><td><strong>Instrumentl, SBIR.gov</strong></td><td>Grant and federal funding
    discovery</td><td>Non-dilutive only, and completely separate from the equity
    question</td></tr>
  <tr><td><strong>ChatGPT with search</strong></td><td>Will cheerfully give you a list
    of fintech investors</td><td>No idea what you are eligible for, and the web data
    underneath it is old, see below</td></tr>
</table>

<p>FinStack does three things none of these do.</p>

<p><strong>It gives you an order, not a list.</strong> The output is a plan across the
next 12 to 18 months, where each step says why it comes before the next one and what it
unlocks. Free money first where it buys the traction an equity investor is going to ask
for. Debt where what you actually need is capital for the loan book.</p>

<p><strong>It separates debt from equity.</strong> The highest-value question on the
form is "do you lend money off your own balance sheet?" Answering yes changes the whole
answer: warehouse providers move to the top of the plan and equity drops below them.</p>

<p><strong>It tells you why they will say no.</strong> One of the agents does nothing
but argue the other side. That is the thing you normally only get from a friend who
happens to be an investor, and never from a directory.</p>

<h3>Why a scraper cannot do this</h3>

<p>I did not want to just assert that human judgement beats scraped data, so here is
what building it actually turned up.</p>

<ul>
  <li>I had an AI agent read all 59 funders' own websites and pull out their criteria.
    It found <strong>stage information for 26 of them</strong>, <strong>check sizes for
    19</strong>, and <strong>licensing expectations for none at all</strong>. Funds
    simply do not publish the things that disqualify you.</li>
  <li>Eleven of the 59 sites had no eligibility information whatsoever. Mostly corporate
    foundations and debt providers, whose websites are brochures.</li>
  <li>When I searched the web for the same information, I got SEO listicles with numbers
    from 2018 to 2022 that contradicted each other.</li>
  <li>Three funders on my list of <em>well-known</em> names turned out to be dead or
    dying. The Financial Solutions Lab is gone. Restive Ventures' website does not load
    on any version of its domain. The FIS accelerator looks like it has wound down.</li>
  <li>Going through the list myself, I cut seven more as inactive or not relevant to
    fintech founders, and marked <strong>eight of the surviving 52 as not currently
    writing checks</strong>.</li>
</ul>

<p>Whether a fund is actually deploying right now does not appear on any website, so I
filled it in by hand for all 52. It is the field most likely to save a founder a wasted
month, and there is no way to scrape it.</p>

<h2>4. The agents</h2>

{img("architecture", "Figure 1. The top row runs once, before anyone uses the app, and builds the funder dataset. The bottom row is what happens when a founder hits submit: four AI calls, with a free filtering step in the middle.", width="92%")}

<h3>What each one does</h3>

<table class="agents">
  <tr><th>Agent</th><th>Job</th><th>What it gets</th><th>What it gives back</th></tr>
  <tr><td><strong>Extractor</strong><br><span class="muted">runs once, offline</span></td>
    <td>Reads a funder's own web pages and pulls out their criteria</td>
    <td>The text of their site</td>
    <td>A structured record where every fact comes with the exact sentence it came from
    </td></tr>
  <tr><td><strong>Intake</strong></td>
    <td>Turns the form answers and anything typed in the free-text box into a profile</td>
    <td>14 answers, plus optional free text</td>
    <td>A tidy profile, plus up to 3 follow-up questions about anything left blank</td></tr>
  <tr><td><strong>Matcher</strong></td>
    <td>Scores the shortlist and says why, quoting the funder's own words</td>
    <td>The profile and 25 funder records</td>
    <td>A score out of 100, reasons, things to watch out for, and whether it is the
      right <em>type</em> of capital</td></tr>
  <tr><td><strong>Planner</strong></td>
    <td>Puts the raise in order</td>
    <td>The top 8 matches</td>
    <td>Up to 4 steps, each naming a funder and what that step unlocks</td></tr>
  <tr><td><strong>Skeptic</strong></td>
    <td>Argues why each top funder will pass on you</td>
    <td>The top 3 matches</td>
    <td>The objection, what would change their mind, and how confident it is</td></tr>
</table>

<p>The agents run one after another in a fixed order, like an assembly line. Intake
passes a profile to the filter, the filter passes a shortlist to the matcher, and the
planner and skeptic both read what the matcher produced. Nothing ever hands work
backwards, which means the app cannot get stuck in a loop. I specifically wanted to
avoid that, since a loop on a shared course key becomes somebody else's problem too.</p>

<p>Each agent gets one request, and it has to fill in a fixed template rather than
writing free-form text. That is what keeps the cost predictable and stops an agent from
wandering off into an essay.</p>

<h3>Why this model</h3>

<p>Everything runs on <strong>gpt-6-luna</strong>, which is the only model the course key
allows, on the lowest reasoning setting. That turned out to be the right choice rather
than a limitation. All five jobs are reading, comparing and writing a few sentences
against evidence I hand them. None of them needs deep reasoning. The one I expected to
struggle was the skeptic, and its objections have been consistently sharp. There is an
example in the traced run below.</p>

<h3>The step that uses no AI at all</h3>

<p>Between intake and matching there is a filter that is just ordinary code, no AI
involved. It takes each funder's facts and checks them against the founder: stage,
sector, type of capital, revenue minimum, licensing, geography, and rules like
student-founders-only. In the run below it took <strong>52 funders down to 31 eligible,
then ranked those and passed the top 25</strong> to the matcher.</p>

<p>Two rules make this safe. <strong>If the founder said "I don't know", that never
rules a funder out</strong>. The funder stays in and gets labelled "needs
confirming", since dropping a good match over a blank field does more harm than showing
it with a caveat. And <strong>a preference is not a rule</strong>: a fund
that says it "emphasises New York companies" is telling you a preference, which should
affect the score, not something that disqualifies you.</p>

<h3>One real run, start to finish</h3>

<p>The founder below is one of three examples built into the app, so anyone can
reproduce this with one click: a seed-stage lender making small-dollar installment loans
to thin-file borrowers, underwriting on cash-flow data, <strong>lending off its own
balance sheet</strong>, licenses in progress, raising $2M.</p>

{img("01_landing", "Figure 2. The landing page. The three example buttons fill in all 14 fields at once, so you can try it without inventing a startup.", width="84%")}

{img("02b_form_standing", "Figure 3. The questions that decide what you are eligible for, filled in from the example. The balance-sheet lending question changes the answer more than anything else on the form, and 'I don't know' is a real option throughout.")}

{img("03_progress", "Figure 4. The run in progress. Each agent ticks off as it finishes. The filtering step is labelled 'no model call' so you can see which part is free.")}

<h3>What came out</h3>

{img("05_plan", "Figure 5. The capital plan. Equity is step 4, behind regulatory prep and two warehouse conversations.", width="84%")}

<p>This was the output I was most interested in seeing. The planner put <strong>getting the
regulatory package together first</strong>, then <strong>i80 Group</strong> and
<strong>Victory Park Capital</strong> for warehouse capital against the loan book, and
<strong>equity last</strong>, saying outright that equity "is not warehouse
capital" and should come after there is lending traction to show. A founder working off
a directory would almost certainly have done it in the opposite order.</p>

{img("06_match_card", "Figure 6. A match card: the score, whether it is the right kind of capital, the funder's own words, and the skeptic's objection, all in one place.", width="90%")}

<p>Look at the skeptic's objection specifically. It is not filler. It asks for
loan-level performance and loss data, points out that the $2M ask mixes operating money
and loan-book money without separating them, and says exactly what would change its mind.
That is feedback a founder would normally only get after being turned down, if they got
it at all.</p>

{img("07_screened_out", "Figure 7. Funders ruled out before any AI ran, each with the reason why.")}

<p>Showing the rejections matters as much as showing the matches. A founder can act on
"Nyca Partners, invests at seed only; you are pre-seed", whereas a list that drops Nyca
without saying why leaves them none the wiser.</p>

<h2>5. Tokenomics: what it costs to run</h2>

<p>Everything here is measured from actual runs. The app shows its own usage at the
bottom of every result page, which is where these numbers come from.</p>

{img("08_cost", "Figure 8. The cost panel from the run above, exactly as the app displays it.", width="90%")}

<table class="nums">
  <tr><th>Agent</th><th>Input</th><th>Cached</th><th>Output</th></tr>
  <tr><td>Intake</td><td>1,232</td><td>0</td><td>714</td></tr>
  <tr><td>Matcher</td><td>5,490</td><td>0</td><td>2,586</td></tr>
  <tr><td>Planner</td><td>2,032</td><td>0</td><td>627</td></tr>
  <tr><td>Skeptic</td><td>863</td><td>0</td><td>562</td></tr>
  <tr class="total"><td>Total for one run</td><td>9,617</td><td>0</td><td>4,489</td></tr>
</table>

<p>Input is everything I send the model; output is what it writes back. Output costs
five times as much, which is why the agents are told to be brief. At gpt-6-luna's rates
of $0.10 per million input tokens and $0.50 per million output:</p>

<table class="nums">
  <tr><th></th><th>Cost</th></tr>
  <tr><td>One founder running it once</td><td>$0.0032</td></tr>
  <tr><td>One founder for a month (3 runs)</td><td>$0.0096</td></tr>
  <tr><td>100 founders a month</td><td>$0.96</td></tr>
  <tr><td>10,000 founders a month</td><td>$96</td></tr>
  <tr><td>Building the whole funder dataset, one time</td><td>$0.0293</td></tr>
</table>

<p>Building the entire dataset cost three cents, and serving a hundred founders for a
month costs under a dollar. Running this is cheap enough that cost is not what limits it.
What limits it is how good the dataset is, and that comes down to human time.</p>

<h3>Three things that keep it cheap</h3>

<p><strong>The filter is ordinary code.</strong> Working out whether a founder is
eligible is a lookup rather than a judgement call, so there is no reason to pay a model
for it. In the run above it cut 52 funders down to 25 before the matcher saw anything.
Sending all 52 would have roughly doubled the matcher's input, so filtering first saves
around 30% of what a run costs, and that saving gets bigger as the dataset grows.
It is the main reason I could add a few hundred more funders without the cost per run
moving much.</p>

<p><strong>The matcher scores all 25 funders in one go</strong> rather than asking about
each one separately. That is the difference between 4 requests per run and 28.</p>

<p><strong>The skeptic only looks at the top 3</strong>, not all 25. Nobody needs a
detailed argument about why the 19th-best match will pass.</p>

<h3>Where cutting cost cost me something</h3>

<p>I measured this rather than assuming it. I ran the same founder twice: once
normally, and once with the filter switched off so the matcher scored all 52 funders.</p>

<table class="nums">
  <tr><th></th><th>Filtered (25)</th><th>Unfiltered (52)</th></tr>
  <tr><td>Matcher input tokens</td><td>5,428</td><td>10,335</td></tr>
  <tr><td>Matcher output tokens</td><td>2,354</td><td>4,357</td></tr>
  <tr><td>Cost of that call</td><td>$0.0017</td><td>$0.0032</td></tr>
  <tr><td>Top 3 matches</td><td colspan="2">identical: i80 Group, Victory Park, Fenway Summer</td></tr>
</table>

<p>So filtering first cuts the matcher call roughly in half, which is where my earlier
30%-of-total-run figure comes from. The top of the list did not move.</p>

<p><strong>It did cost something, though.</strong> Portage appeared fourth in the
unfiltered run with a score of 77, and never appeared at all in the filtered run. It was
not ruled out as ineligible; it passed the eligibility check and then lost the cut to 25
on ranking. The reason it ranked low is that its extracted record is empty: its website
never stated which stages it invests at or which parts of fintech it covers, so there was
almost nothing for the cheap ranking to score it on.</p>

<p>That is the real trade, and it is sharper than I expected. The cost-saving step does
not penalise funders who are a poor fit. It penalises funders whose websites say little,
which is a different thing and not one a founder would want. Raising the shortlist to
about 35 would close most of the gap and still cost less than sending everything; the
better fix is filling in the missing fields by hand, which is the same conclusion as
everywhere else in this report.</p>

<p><strong>Caching is doing nothing during a run, and the table above shows it as
zero.</strong> Caching is when the provider recognises that you have sent the same chunk
of text before and charges you a tenth as much for it. It only kicks in once that
repeated chunk is big enough, and each of my four agents has its own short set of
instructions, so none of them clears the bar. The dataset build <em>does</em> benefit:
63,220 of its 179,877 input tokens were cached, because there the same long
instruction goes out 59 times in a row. To get it working during a run I would need to
reorder what I send the matcher so the funder list comes before the founder's details,
since the funder list is the part that stays the same. I have not done it. At a third of
a cent per run the money is not the reason to bother; the reason is that the matcher is
57% of the cost and it is the only part that grows as the dataset does.</p>

<h2>6. Safety</h2>

<p>Six things could go wrong with this app. There is a defense built for each one, and
a script in the repo (<code>tests/safety_checks.py</code>) that attacks the app on
purpose and reports whether each defense held. It currently passes <strong>7 of 7
checks</strong>. I wrote it to report failures rather than hide them, and one of the
findings below came from a check that failed.</p>

<table class="compare">
  <tr><th>What could go wrong</th><th>Why it matters here</th><th>What stops it</th></tr>
  <tr><td>Someone types instructions into the form to manipulate the app</td>
    <td>There is a free-text box, and the agents read it</td>
    <td>The text is handed over clearly labelled as information, not orders, plus the
      two checks below</td></tr>
  <tr><td>An agent makes up a fund that does not exist</td>
    <td>A fake fund or deadline costs a founder a real week</td>
    <td>Every fund named gets checked against my list. Anything not on it is thrown
      away</td></tr>
  <tr><td>An agent makes up a number</td>
    <td>A wrong check size sends a founder into the wrong room</td>
    <td>Quotes have to actually appear on the funder's page, and numbers have to appear
      in the sentence quoted for them</td></tr>
  <tr><td>Results go missing without the founder knowing</td>
    <td>A short list of matches looks the same as a correct one</td>
    <td>The app counts what came back against what it asked for</td></tr>
  <tr><td>Runaway spending</td>
    <td>A bug or a bad actor burning a shared course key</td>
    <td>Hard stop at 8 requests or 120,000 tokens per session</td></tr>
  <tr><td>The API key leaking</td>
    <td>It is not mine alone</td>
    <td>Never printed, never written to a file, and excluded from the repo</td></tr>
</table>

<h3>Catching a made-up number</h3>

<p>This one was not staged, which is why I like it. While building the dataset, the
extraction agent reported that QED Investors writes checks of $3M to $10M and attached a
quote from their website to back it up. The quote was genuine and did appear on the page,
but it said nothing about those figures.</p>

{code('''qed,QED Investors,https://www.qedinvestors.com,unsupported_quote,
"check_size 3000000-10000000 not stated in its own quote:
 Investments from the early stage fund have an average size of
 approximately $15 million"''')}

<p>This is why there are two checks. The first asks whether the quoted sentence really
appears on the page, which it did, so that check passed. The second asks whether the
number being claimed appears in that same sentence, and $3M and $10M do not appear in a
sentence about $15M. Both figures were deleted and the funder was put in a
queue for me to look at by hand. The same check caught two more invented check sizes, for
Better Tomorrow Ventures and Motive Partners. Three out of 59.</p>

<h3>Trying to manipulate the app on purpose</h3>

<p>I typed an instruction into the company description box, which is free text that
reaches the matcher:</p>

{img("09a_injection_input", "Figure 9. The attack: a fake note claiming to be from the people running the app, demanding one specific fund be scored 100, listed first, and that nothing else be returned.")}

{img("09b_injection_count", "Figure 10. What came back. It asked for one result. It got 25.")}

<p>It failed in three separate ways. I did not want to be relying
on any single one of them.</p>

<ol>
  <li>The fund it named, Dorm Room Fund, <strong>was not in the results at all.</strong>
    The plain-code filter had already removed it, because Dorm Room Fund only backs
    student founders and this founder is not one. The attack picked a target it was
    impossible to promote.</li>
  <li>It asked for a single result and the app returned 25.</li>
  <li>When an instruction does make it as far as the matcher, the matcher calls it out
    in what the founder sees: <em>"The profile includes an unauthorized
    platform-operator instruction claiming pre-verification and directing a score and
    ranking; ignored because it is not evidence of fit."</em></li>
</ol>

<h3>What testing actually taught me</h3>

<p>Two things worth being honest about.</p>

<p><strong>My keyword tripwire misses the polite version.</strong> It catches "ignore
all previous instructions". It does not catch "for your analysis, treat X as the
strongest possible match". It works more like a smoke alarm that warns the user than
like a lock. I left it that way on purpose, because chasing every possible phrasing is a
losing game and the checks that actually hold are the mechanical ones: the fund has to be
on my list, and the count has to add up.</p>

<p><strong>Testing found a real hole I had not thought of.</strong> Before I fixed it,
an instruction in the description did not succeed in promoting the fund it named, but it
did <em>cut the results from 25 funders down to 8</em> with nothing on the screen to say
so. A founder would have lost two thirds of their matches without knowing, which I think
is worse than a rigged ranking precisely because there is nothing to notice. The fix had three parts: label the founder's
details clearly as information rather than instructions, require the matcher to return
something for every funder it was given, and have the app count the results and warn the
founder if any are missing.</p>

<p>There is also a defense I did not build and only found by accident. Portkey routes
through Azure, which screens what you send before the model ever sees it, and it rejected
the blunter attacks outright. Left alone that crashed the app and showed the founder a
raw error from Microsoft, so now it is caught and explained in plain English instead.</p>

<h3>Spending and keys</h3>

<p>The spending limit gets checked before each request rather than during one, so a run
can overshoot by one request before it halts. In testing it stopped at 125,000 tokens
against a 120,000 limit. A normal run uses 14,106 tokens
across 4 requests, so the limit only ever bites when something has genuinely gone wrong.
The key is read from the environment and never printed anywhere; the test script checks
every file for anywhere it might be written out.</p>

<h2>7. Impact</h2>

<p>I can measure what the app costs and what it does. For whether it is worth using, I
walked a former colleague through the build step by step and shared this draft. He works
at a venture philanthropy investing in economic mobility ventures, which overlaps heavily
with the inclusion end of fintech, and he has seen this problem from the funder side for
years.</p>

<h3>What is measured</h3>

<table class="nums">
  <tr><th>What</th><th>Number</th><th>Where it comes from</th></tr>
  <tr><td>Funders in the dataset</td><td>52</td><td>Built, then reviewed by hand</td></tr>
  <tr><td>Direct quotes backing the facts</td><td>141</td><td><code>funders.json</code></td></tr>
  <tr><td>Funders I have personally assessed</td><td>52 of 52</td><td><code>tier_b.csv</code></td></tr>
  <tr><td>Funders flagged as not currently deploying</td><td>8</td><td>My judgement</td></tr>
  <tr><td>Dead or dying programs found and removed</td><td>3</td><td>Broken sites, checked</td></tr>
  <tr><td>More funders cut as not relevant</td><td>7</td><td>My review</td></tr>
  <tr><td>Made-up figures caught before anyone saw them</td><td>3</td><td><code>review_queue.csv</code></td></tr>
  <tr><td>Time to a full capital plan</td><td>Under a minute</td><td>Measured</td></tr>
  <tr><td>Cost per founder served</td><td>$0.0032</td><td>Measured</td></tr>
</table>

<h3>What that is worth to a founder</h3>

<ul>
  <li><strong>About a week of founder time, from one field.</strong> All eight funders I
    marked as not currently deploying have live, well-maintained websites, so a scraper
    or ChatGPT would recommend every one of them. At half a day of research and outreach
    each, which I think is conservative, that is roughly a week spent on conversations
    that cannot end in a check.</li>
  <li><strong>Points of dilution, for balance-sheet lenders.</strong> A founder who
    raises equity instead of a warehouse facility gives away ownership to fund assets
    that debt would have funded more cheaply. How big that is depends on the raise, but
    it shows up in ownership rather than in hours.</li>
  <li><strong>Three wrong numbers that never reached anyone.</strong> The checks caught
    invented check sizes for QED, Better Tomorrow Ventures and Motive Partners during the
    build. Any one of them would have sent a founder into the wrong conversation.</li>
  <li><strong>Negligible cost to run.</strong> A third of a cent per founder, and three
    cents to build the entire dataset.</li>
</ul>

<h3>What the practitioner review said</h3>

<ul>
  <li><strong>The information gap is real and deliberate.</strong> Funds keep their own
    private databases of peer investors and what those peers require, along with call
    notes from fund-to-fund conversations, and they share diligence material among
    themselves. None of it is public.</li>
  <li><strong>Founders only get this through relationships.</strong> Which is hardest
    exactly when you need it most, as someone early or raising for the first time.</li>
  <li><strong>It matters more to under-resourced teams.</strong> Early-stage founders
    often have a small, inexperienced, or non-existent team helping them plan a raise, so
    cutting out wasted work is worth more to them than to a better-resourced company.</li>
  <li><strong>Better than a generic LLM for this question.</strong> His words, and a
    direct answer to the obvious objection.</li>
  <li><strong>The dataset gets stronger the more network knowledge goes into it.</strong>
    He agreed with the direction I had already identified as the main weakness.</li>
  <li><strong>Two warnings (also in Section 8).</strong> Some funders are vague about
    their thesis on purpose, so this needs constant updating to stay accurate. And there
    is a real question about how much network knowledge I should publish without damaging
    the relationships that produced it.</li>
</ul>

<h2>8. Limits and what is next</h2>

<h3>What does not work yet</h3>

<ul>
  <li><strong>52 funders is not the market.</strong> It covers US fintech decently but it
    is not everything, and it is a snapshot of right now. Every record has a date on it
    for that reason.</li>
  <li><strong>The data is patchy in places.</strong> Stage information for 26 of 52,
    check sizes for 19. The app says "not assessed" rather than guessing, which is the
    right call but does mean some matches rest on less evidence than others.</li>
  <li><strong>Some funders are vague on purpose.</strong> A practitioner who reviewed
    this pointed out that plenty of funds keep their stated thesis and current priorities
    deliberately broad, which is a choice rather than an oversight. A dataset like mine
    is therefore chasing a moving target and will be noticeably stale within a year if
    nobody maintains it.</li>
  <li><strong>There is a limit to what I should publish.</strong> The same reviewer
    raised something I had not thought about: the most valuable entries in the dataset
    would come from what I know through my network, and putting all of that into a public
    tool could damage the relationships that produced it. Figuring out where that line
    sits is a real constraint on how good this can get, and it is not a technical
    one.</li>
  <li><strong>One person has assessed all of it.</strong> My judgement is the
    differentiator and also the single point of failure.</li>
  <li><strong>Nothing is saved.</strong> Results live in memory and vanish when the
    server restarts.</li>
  <li><strong>No warm intros.</strong> The app tells you who fits and why they might
    pass, but not who can introduce you, which is still how most of this really
    works.</li>
</ul>

<h3>What I would build next</h3>

<ol>
  <li><strong>A real cost-of-capital number.</strong> The fields are already there
    (dilution, reporting hours, how long diligence takes), but I have only filled in the
    timing for two funders. With fuller coverage the app could rank by what
    the money actually costs you rather than by fit alone. This is the feature I most
    want and it needs time, not code.</li>
  <li><strong>Get caching working during a run</strong>, by reordering what gets sent to
    the matcher, as described in section 5.</li>
  <li><strong>An investor-side version.</strong> When a fund passes on a company, it
    could route that founder to the funders who do fit, turning a rejection into a
    referral. The matching is the hard part and it already exists.</li>
  <li><strong>Re-check everything monthly.</strong> Rebuilding the dataset costs three
    cents, so there is no reason not to re-run it and flag anything whose website has
    changed.</li>
  <li><strong>More people assessing funders</strong>, with each judgement attributed, so
    it does not all rest on me.</li>
</ol>

<hr>
<p class="footer">I built this by directing AI coding tools, and the code in the
repository was written that way. What I brought is the judgement about fintech funding: which funders belong in the dataset, which of them are
actually deploying, what rules out a founder, and whether the output is any good. Every
figure in this report is measured from real runs of the app, and the logs, the review
queue and the safety test output are all in the repository.</p>
"""

HTML = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>FinStack &mdash; MGT 409 Final Project</title>
<style>
  :root{{--navy:#13262F;--sage:#90A583;--mauve:#7A6263;--mauve-deep:#5E4A4B;
    --paper:#FAF7F5;--line:#E6DEDB;--muted:#6E6668;--mauve-soft:#F4EBEA;--sage-soft:#EDF1E9;}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:#fff;color:var(--navy);
    font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}}
  .page{{max-width:860px;margin:0 auto;padding:0 48px 80px}}
  .cover{{background:var(--navy);color:var(--paper);padding:52px 48px 40px;margin-bottom:44px}}
  .cover .eyebrow{{font-size:12px;letter-spacing:.2em;text-transform:uppercase;
    color:var(--sage);margin:0 0 14px;font-weight:700}}
  .cover h1{{font-size:52px;margin:0 0 10px;letter-spacing:-.03em;font-weight:800}}
  .cover .sub{{font-size:19px;max-width:48ch;margin:0 0 26px;color:#DED5D3}}
  table.meta{{border-collapse:collapse;font-size:14px}}
  table.meta td{{padding:4px 22px 4px 0;vertical-align:top;color:#DED5D3}}
  table.meta td:first-child{{color:var(--sage);font-weight:700;white-space:nowrap}}
  h2{{font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:var(--mauve);
    font-weight:800;margin:52px 0 16px;padding-bottom:9px;border-bottom:2px solid var(--mauve-soft)}}
  h3{{font-size:18px;margin:30px 0 10px;letter-spacing:-.01em}}
  p{{margin:0 0 14px}}
  ul,ol{{margin:0 0 16px;padding-left:22px}} li{{margin:6px 0}}
  code{{background:var(--mauve-soft);padding:1px 5px;border-radius:3px;font-size:13px}}
  code.todo{{background:#FFF3CD;color:#7a5c00}}
  /* code on the dark cover needs light text on a dark chip */
  .cover code{{background:rgba(255,255,255,.14);color:#fff;border:1px solid rgba(255,255,255,.2)}}
  .cover a{{color:#B7C9AC;text-decoration:none;border-bottom:1px solid rgba(183,201,172,.45)}}
  .cover code.todo{{background:#FFF3CD;color:#7a5c00;border-color:#E0C067}}
  pre{{background:var(--navy);color:#E8EDEA;padding:16px 18px;border-radius:4px;
    font-size:12.5px;line-height:1.5;overflow-x:auto;margin:0 0 16px}}
  table{{border-collapse:collapse;width:100%;margin:0 0 20px;font-size:14px}}
  th{{text-align:left;font-size:11px;letter-spacing:.1em;text-transform:uppercase;
    color:var(--mauve);border-bottom:2px solid var(--mauve-soft);padding:7px 10px 7px 0}}
  td{{padding:9px 10px 9px 0;border-bottom:1px solid var(--line);vertical-align:top}}
  table.nums td:not(:first-child),table.nums th:not(:first-child){{text-align:right}}
  tr.total td{{font-weight:700;border-bottom:2px solid var(--mauve)}}
  figure{{margin:22px 0 26px}}
  figure img{{display:block;border:1px solid var(--line);border-radius:4px}}
  figcaption{{font-size:13px;color:var(--muted);margin-top:9px;line-height:1.45}}
  .muted{{color:var(--muted);font-size:12px}}
  .todo-block{{background:#FFF8E6;border-left:4px solid #D8A62B;padding:14px 18px;
    margin:0 0 16px}}
  hr{{border:0;border-top:2px solid var(--mauve-soft);margin:44px 0 20px}}
  .footer{{font-size:13px;color:var(--muted)}}
  @media print{{
    @page{{margin:0.55in}}
    body{{font-size:10pt;line-height:1.45}}
    .page{{padding:0 0 0.2in}}
    .cover{{padding:26px 30px 22px;margin-bottom:22px}}
    .cover h1{{font-size:34pt}} .cover .sub{{font-size:12pt}}
    h2{{page-break-after:avoid;margin:22px 0 9px}}
    h3{{page-break-after:avoid;margin:16px 0 6px;font-size:12pt}}
    p{{margin:0 0 8px}} ul,ol{{margin:0 0 9px}} li{{margin:3px 0}}
    /* images dominated the page count; cap them so text and figures share space */
    figure{{page-break-inside:avoid;margin:12px 0 14px}}
    figure img{{max-height:3.1in;width:auto !important;max-width:100%}}
    figcaption{{font-size:8.5pt;margin-top:5px}}
    table{{page-break-inside:avoid;font-size:9pt}}
    td{{padding:5px 8px 5px 0}} th{{padding:5px 8px 5px 0}}
    pre{{font-size:8.5pt;padding:10px 12px}}
  }}
</style></head>
<body>{BODY.split('</header>')[0]}</header>
<div class="page">{BODY.split('</header>', 1)[1]}</div>
</body></html>"""

OUT.write_text(HTML, encoding="utf-8")
kb = OUT.stat().st_size // 1024
print(f"wrote {OUT.name}  ({kb:,} KB, {HTML.count('<figure>')} figures)")
