#!/usr/bin/env python3
"""Grade the tools against what Lismore City Council actually decided.

ROADMAP.md Phase T, item T8. Every audit in `scripts/` checks this server's data
against the documents *we* hold, and the scenario suites are graded by us. This
is the one check graded by someone else: Council's Notices of Determination,
published on its DA Tracker. It found things no document audit can — Council
practice (a Flood Evacuation Plan on most floodplain consents), the Section 64
charge the repo never sized, real turnaround — and a bug 1,346 tests missed.

Four modes, run in this order as a loop:

  harvest   List business DAs on the tracker that are not yet cases.
  fetch     Download a DA's detail page and notice into the cache, read
            Council's figures off the notice, and (with --update) record them
            in the case file.
  grade     Run every case through the tools and grade the answers against
            Council's figures. Writes a report into the cache.
  freeze    For a case Council has not determined yet, record what the tools
            say *now*, so `grade` can later mark a prediction made without
            hindsight. This is the honest version of the test: grading after
            the fact lets the grader pick inputs that fit the answer.

Case inputs live in `tests/fixtures/tracker_cases.json` and are written by hand
(or by the `tracker-validator` agent) from **only what the applicant knew at
lodgement** — the tracker's description and the lodged documents, never the
consent. That file is committed; it holds public record only (DA number,
property address, Council's figures) and never a name.

Privacy: notices carry the applicant's name, address and email. Everything
downloaded goes to `tracker-cache/`, which `.gitignore` excludes and
`.claude/hooks/protect-private-paths.py` refuses to stage.

Scraping quirks, learned the hard way (SCRAPER.md has the council site's):
  * The tracker is Civica/Altitude and 403s plain HTTP — Playwright, like the
    council site. Needs `uv sync --extra scraping`.
  * `daEnquiry.do` accepts a GET, but ignores its date filters and caps near
    150 results, so harvest searches street by street and filters locally.
  * Some contribution tables are images. Those are reported as unreadable,
    never guessed.
  * Council's property address and the state geocoder's address point can
    differ by a street number. A case can carry `zone_override` with a note
    saying where the zone came from.

Usage:
  .venv/bin/python scripts/validate_against_tracker.py harvest [--since 2024-07-01] [--streets Keen Molesworth]
  .venv/bin/python scripts/validate_against_tracker.py fetch 2026/15/1 [--update]
  .venv/bin/python scripts/validate_against_tracker.py grade [2026/15/1 ...]
  .venv/bin/python scripts/validate_against_tracker.py freeze 2026/250/1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import urllib.parse
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

CASES_FILE = ROOT / "tests" / "fixtures" / "tracker_cases.json"
CACHE = ROOT / "tracker-cache"

BASE = "https://www.lismore-nsw.altitudelg.com/e-services/"
SEARCH_INIT = BASE + "daEnquiryInit.do?doc_typ=5&nodeNum=162748"
RECENTLY_DETERMINED = BASE + "daEnquiry/recentlyDetermined.do?num_days={days}&nodeNum=162747"
RECENTLY_LODGED = BASE + "daEnquiry/recentlySubmitted.do?rangeType=M&rangeFrom={months}&rangeTo=0&nodeNum=162746"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# The streets the CBD and the commercial and industrial areas are on. A street
# search is the only way past the result cap; add streets rather than widening.
BUSINESS_STREETS = [
    "Keen", "Molesworth", "Woodlark", "Magellan", "Conway", "Carrington", "Union",
    "Ballina", "Bridge", "Casino", "Uralba", "Dawson", "Zadoc", "Bruxner", "Wilson",
    "Terania", "Brewster", "Hunter", "Diadem", "Cullen", "Oliver", "Krauss", "Kyogle",
    "Dalley", "Military", "Orion", "Cook", "Engine", "Three Chain", "Elliott", "Laurel",
    "Eggins", "Nimbin", "Dunoon",
]

BUSINESS = re.compile(
    r"shop|cafe|café|restaurant|food|\bbar\b|pub|hotel|office|business|commercial|"
    r"retail|warehouse|industr|gym|recreation|change of use|sign|child ?care|medical|"
    r"health|premises|workshop|storage|vehicle|brew|takeaway|salon|barber|tattoo|clinic",
    re.I,
)
# Word boundaries matter: a bare "tree" matched every description naming a Street.
NOT_BUSINESS = re.compile(
    r"\bdwellings?\b|\bsecondary\b|\bgranny\b|\bsubdivision\b|\bpool\b|\bcarport\b|"
    r"4\.55|96\(|\bmodif|\bdemoli|\btrees?\b|dual occ|manufactured home|residential flat",
    re.I,
)

ADDRESS_LINE = re.compile(r"^(.+NSW\s+24\d\d)\s*$", re.M)


# ---------------------------------------------------------------------------
# Cases file
# ---------------------------------------------------------------------------

def load_cases() -> dict:
    if not CASES_FILE.exists():
        return {"_about": "", "cases": {}}
    return json.loads(CASES_FILE.read_text())


def save_cases(data: dict) -> None:
    data["cases"] = dict(sorted(data["cases"].items()))
    CASES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Tracker pages
# ---------------------------------------------------------------------------

def parse_listing(text: str) -> list[dict]:
    """Records from a tracker result page. The applicant is deliberately not read."""
    body = text.split("Documents Found", 1)[-1]
    starts = list(ADDRESS_LINE.finditer(body))
    records = []
    for i, m in enumerate(starts):
        block = body[m.end(): starts[i + 1].start() if i + 1 < len(starts) else len(body)]

        def field(label: str, block: str = block) -> str | None:
            hit = re.search(rf"{re.escape(label)}\s*\n+(.+)", block)
            return hit.group(1).strip() if hit else None

        number = field("Application No.")
        if not number:
            continue
        records.append({
            "da": number,
            "address": re.sub(r"\s+", " ", m.group(1)).strip(),
            "description": field("Type of Work") or "",
            "lodged": field("Date Lodged"),
            "cost": field("Cost of Work"),
            "determination": field("Determination Details"),
            "determined": field("Determination Date"),
        })
    return records


def _date(value: str | None) -> date | None:
    try:
        return datetime.strptime(value, "%d/%m/%Y").date() if value else None
    except ValueError:
        return None


def is_business(record: dict) -> bool:
    text = record["description"]
    return bool(BUSINESS.search(text)) and not NOT_BUSINESS.search(text)


async def _browser():
    try:
        from playwright.async_api import async_playwright  # noqa: PLC0415
    except ImportError:
        sys.exit("Playwright is not installed. Run: uv sync --extra scraping "
                 "&& .venv/bin/playwright install chromium")
    pw = await async_playwright().start()
    browser = await pw.chromium.launch()
    ctx = await browser.new_context(user_agent=UA)
    return pw, browser, ctx


async def _search(page, **params) -> str:
    query = dict(number="", dateFrom="", dateTo="", detDateFrom="", detDateTo="",
                 streetName="", suburb="", unitNum="", houseNum="", planNumber="",
                 strataPlan="", lotNumber="", propertyName="", searchMode="A",
                 submitButton="Search")
    query.update(params)
    await page.goto(SEARCH_INIT, wait_until="networkidle", timeout=60000)  # sets the session
    await page.goto(BASE + "daEnquiry.do?" + urllib.parse.urlencode(query),
                    wait_until="networkidle", timeout=90000)
    return await page.inner_text("body")


async def harvest(streets: list[str], since: date) -> list[dict]:
    pw, browser, ctx = await _browser()
    page = await ctx.new_page()
    found: dict[str, dict] = {}
    try:
        pages = [(f"street {s}", None, s) for s in streets]
        pages += [("recently determined", RECENTLY_DETERMINED.format(days=90), None),
                  ("recently lodged", RECENTLY_LODGED.format(months=3), None)]
        for label, url, street in pages:
            try:
                if url:
                    await page.goto(url, wait_until="networkidle", timeout=90000)
                    text = await page.inner_text("body")
                else:
                    text = await _search(page, streetName=street)
            except Exception as exc:  # one page failing must not lose the rest
                print(f"  {label}: failed ({type(exc).__name__})", file=sys.stderr)
                continue
            rows = parse_listing(text)
            print(f"  {label}: {len(rows)}", file=sys.stderr)
            for row in rows:
                found[row["da"]] = row
    finally:
        await browser.close()
        await pw.stop()
    return [r for r in found.values()
            if (_date(r["lodged"]) or date.min) >= since and is_business(r)]


async def fetch(numbers: list[str]) -> dict[str, dict]:
    """Detail page and documents for each DA, saved under the cache."""
    pw, browser, ctx = await _browser()
    page = await ctx.new_page()
    out = {}
    try:
        for number in numbers:
            year, seq, stage = number.split("/")
            key = number.replace("/", "-")
            folder = CACHE / key
            folder.mkdir(parents=True, exist_ok=True)
            text = await _search(page, number=f"{seq}/{year}")
            if "Below are the details" not in text:
                listed = [r["da"] for r in parse_listing(text)]
                links = await page.eval_on_selector_all(
                    "a[href*='daEnquiryDetails']", "els => els.map(e => e.getAttribute('href'))")
                if number not in listed:
                    print(f"  {number}: not found on the tracker", file=sys.stderr)
                    continue
                await page.goto("https://www.lismore-nsw.altitudelg.com" + links[listed.index(number)],
                                wait_until="networkidle", timeout=60000)
                text = await page.inner_text("body")
            (folder / "detail.txt").write_text(text)
            docs = await page.eval_on_selector_all(
                "table[summary^='Electronic'] a",
                "els => els.map(e => [e.innerText.trim(), e.getAttribute('href')])")
            saved = []
            for i, (name, href) in enumerate(d for d in docs if not d[0].endswith("Mb")):
                resp = await ctx.request.get("https://www.lismore-nsw.altitudelg.com" + href,
                                             timeout=120000)
                pdf = folder / f"doc{i}.pdf"
                pdf.write_bytes(await resp.body())
                saved.append({"name": name, "file": pdf.name})
            (folder / "documents.json").write_text(json.dumps(saved, indent=1))
            out[number] = {"detail": text, "documents": saved}
            print(f"  {number}: {len(saved)} document(s)", file=sys.stderr)
    finally:
        await browser.close()
        await pw.stop()
    return out


# ---------------------------------------------------------------------------
# Reading Council's figures off a notice
# ---------------------------------------------------------------------------

def _money(text: str) -> float:
    return float(text.replace("$", "").replace(",", "").strip())


def _pdf_text(path: Path) -> str:
    import fitz  # noqa: PLC0415
    with fitz.open(path) as doc:
        return re.sub(r"\s+", " ", " ".join(p.get_text() for p in doc))


def council_facts(number: str) -> dict:
    """What Council decided, read from the cached detail page and notice.

    Only facts about the decision are kept — never the applicant, officer or
    any contact detail — because this dict is written into a committed file.
    """
    folder = CACHE / number.replace("/", "-")
    detail = (folder / "detail.txt").read_text()
    docs = json.loads((folder / "documents.json").read_text())

    def field(label: str) -> str | None:
        hit = re.search(rf"{re.escape(label)}\s*\n+(.+)", detail)
        return hit.group(1).strip() if hit else None

    lodged, determined = _date(field("Date Lodged")), _date(field("Determination Date"))
    stages = re.findall(r"\n\s*([A-Z][^\n\t]+?)\t+\t*(\d\d/\d\d/\d{4})", detail)
    facts = {
        "description": field("Type of Work"),
        "determination": field("Determination Details"),
        "lodged": lodged.isoformat() if lodged else None,
        "determined": determined.isoformat() if determined else None,
        "days": (determined - lodged).days if lodged and determined else None,
        "information_request": any("Additional Information" in s for s, _ in stages),
        "returned": any("Returned" in s for s, _ in stages),
        "notice": False,
    }
    notice = [d for d in docs if d["name"].startswith("Notice of Determination - ")]
    if not notice:
        return facts
    text = " ".join(_pdf_text(folder / d["file"]) for d in notice)
    facts["notice"] = True

    # Section 7.11. No condition at all means nil; a condition whose table
    # cannot be read (it is an image) is unknown, never zero.
    total = re.search(r"APPLICABLE TOTAL ?CONTRIBUTION \$ ?([\d,]+\.\d\d)", text)
    if total:
        facts["s711_total"] = _money(total.group(1))
    elif "Section 7.11" in text or "7.11 Contributions" in text:
        facts["s711_total"] = None
        facts["s711_note"] = "condition present, table not readable (likely an image)"
    else:
        facts["s711_total"] = 0.0

    # Section 64: each line is levy area, ETs, cost per ET, receipt code, amount.
    # Anchor on the table's first line, not its heading — conditions cite the
    # heading by name ("see 'Table - ... Section 64 Contributions'") pages earlier.
    # Take the last table: a notice can carry an earlier quarter's and a re-indexed one.
    tables = list(re.finditer(r"Lismore Water [\d.]+ \$", text)) if "Section 64" in text else []
    table = tables[-1] if tables else None
    if table:
        block = text[max(0, table.start() - 300): table.start() + 900]
        lines = re.findall(r"(Lismore Water|Rous County Council|Lismore Sewer) "
                           r"([\d.]+) ?\$ ?([\d,]+\.\d\d)", block)
        facts["s64_lines"] = [{"levy": levy, "ets": float(e), "per_et": _money(r)}
                              for levy, e, r in lines]
        # Where a policy reduces the charge the table prints two totals: levied, then payable.
        tot = re.search(r"Total \$ ?([\d,]+\.\d\d)(?: \$ ?([\d,]+\.\d\d))?", block)
        facts["s64_total"] = _money(tot.group(1)) if tot else None
        if tot and tot.group(2):
            facts["s64_payable"] = _money(tot.group(2))
        if "Policy 11.3.3" in block:
            facts["s64_note"] = "Policy 11.3.3 in effect (amount payable may be reduced)"
    elif "Section 64" in text:
        facts["s64_total"] = None
        facts["s64_note"] = "Section 64 mentioned, table not readable"
    else:
        facts["s64_total"] = 0.0

    facts["flood_evacuation_plan"] = "Flood Evacuation Plan" in text
    facts["hours_conditioned"] = bool(re.search(r"hours of operation", text, re.I))
    fpl = re.search(r"flood planning level (?:\(FPL\) )?of ([\d.]+) ?m ?\(?AHD", text, re.I)
    if fpl:
        facts["flood_planning_level_m_ahd"] = float(fpl.group(1))
    return facts


# ---------------------------------------------------------------------------
# Running the tools
# ---------------------------------------------------------------------------

async def _call(name: str, args: dict) -> dict:
    from lismore_da_mcp.server import call_tool  # noqa: PLC0415
    try:
        return json.loads((await call_tool(name, args))[0].text)
    except Exception as exc:  # a crash is a result worth reporting, not a stop
        return {"_exception": repr(exc)}


async def run_tools(case: dict) -> dict:
    """What the tools say, from the case's inputs alone."""
    inp = case["inputs"]
    zone_answer = await _call("lookup_zone_by_address", {"address": case["address"]})
    zone = zone_answer.get("zone_code") or inp.get("zone_override")
    out = {"zone": zone, "zone_resolved_by_address": bool(zone_answer.get("zone_code"))}

    if inp.get("sign_type"):
        args = {"sign_type": inp["sign_type"]}
        if zone:
            args["zone_code"] = zone
        if inp.get("height_m"):
            args["height_m"] = inp["height_m"]
        sign = await _call("get_signage_requirements", args)
        need = sign.get("do_you_need_an_application") or {}
        out["sign_pathway"] = need.get("pathway") or ("unrecognised" if "error" in sign else None)
        return out

    use = inp["proposed_use"]
    if zone:
        perm = await _call("check_permissibility", {"zone_code": zone, "land_use": use})
        out["permissibility"] = perm.get("permissibility")

    catchment = inp.get("catchment", "urban")
    fees_args = {"development_cost": inp.get("development_cost", 0),
                 "development_type": use, "catchment": catchment}
    for src, dst in (("floor_area_sqm", "gross_floor_area_m2"), ("existing_use", "existing_use"),
                     ("existing_floor_area_sqm", "existing_gross_floor_area_m2")):
        if inp.get(src) is not None:
            fees_args[dst] = inp[src]
    if not inp.get("development_cost"):
        fees_args["involves_building_work"] = False
    fees = await _call("calculate_da_fees", fees_args)
    parts = fees.get("parts", {})
    s711 = parts.get("section_7_11_contributions", {})
    figure = (s711.get("net_contribution") or s711.get("contribution") or {})
    out["s711"] = figure.get(catchment) if isinstance(figure, dict) else None
    out["s64_sized"] = (parts.get("section_64_water_and_wastewater") or {}).get("amount") is not None

    ready_args = {"proposed_use": use, "property_address": case["address"]}
    for key in ("existing_use", "development_type", "floor_area_sqm", "num_employees",
                "seats", "spaces_provided", "documents_prepared"):
        if inp.get(key) is not None:
            ready_args[key] = inp[key]
    if inp.get("zone_override"):
        ready_args["zone_code"] = inp["zone_override"]
    readiness = await _call("check_da_readiness", ready_args)
    approvals = await _call("get_other_approvals", {"proposed_use": use})
    said = json.dumps([readiness, approvals]).lower()
    out["mentions_flood_evacuation_plan"] = "evacuation plan" in said
    return out


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

def grade(council: dict, tool: dict) -> dict:
    """One verdict per question. PASS / FAIL / GAP (no answer) / INFO."""
    g = {}
    approved = (council.get("determination") or "").lower().startswith(("conditional", "approved"))

    if "permissibility" in tool:
        p = tool["permissibility"] or "none"
        if approved and "prohibited" in p and "likely" not in p:
            g["permissibility"] = f"FAIL — {p}, but Council approved it"
        elif p in ("not_found", "none") or "unrecognised" in p:
            g["permissibility"] = f"GAP — {p}"
        else:
            g["permissibility"] = f"PASS — {p}"

    if "sign_pathway" in tool:
        g["sign_pathway"] = (f"INFO — tool says {tool['sign_pathway']}; this one went by DA"
                             if tool["sign_pathway"] not in ("development_application", "consent")
                             else "PASS")

    if "s711" in tool and council.get("notice"):
        want, got = council.get("s711_total"), tool["s711"]
        if want is None:
            g["s711"] = "INFO — Council's figure unreadable"
        elif got is None:
            g["s711"] = f"GAP — no figure (Council: ${want:,.2f})"
        elif abs(got - want) <= max(10.0, 0.01 * want):
            g["s711"] = f"PASS — ${got:,.2f} vs ${want:,.2f}"
        elif got < want:
            g["s711"] = f"FAIL — understates: ${got:,.2f} vs ${want:,.2f}"
        else:
            g["s711"] = f"FAIL — overstates: ${got:,.2f} vs ${want:,.2f}"

    if council.get("s64_total"):
        g["s64"] = ("PASS — sized" if tool.get("s64_sized")
                    else f"GAP — not sized (Council: ${council['s64_total']:,.2f})")

    if council.get("flood_evacuation_plan"):
        g["flood_evacuation_plan"] = ("PASS" if tool.get("mentions_flood_evacuation_plan")
                                      else "GAP — required by Council, never mentioned")
    if council.get("days") is not None:
        g["days"] = f"INFO — {council['days']} days" + (
            ", with an information request" if council.get("information_request") else "")
    return g


def _summary(grades: dict[str, dict]) -> str:
    counts: dict[str, dict[str, int]] = {}
    for g in grades.values():
        for question, verdict in g.items():
            word = verdict.split()[0]
            counts.setdefault(question, {}).setdefault(word, 0)
            counts[question][word] += 1
    return "\n".join(f"  {q:24} " + "  ".join(f"{k} {v}" for k, v in sorted(c.items()))
                     for q, c in counts.items())


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_harvest(args) -> int:
    since = date.fromisoformat(args.since)
    rows = asyncio.run(harvest(args.streets or BUSINESS_STREETS, since))
    known = load_cases()["cases"]
    new = [r for r in rows if r["da"] not in known]
    print(f"\n{len(rows)} business DA(s) lodged since {since}; {len(new)} not yet cases.\n")
    for r in sorted(new, key=lambda r: _date(r["lodged"]) or date.min):
        state = r["determination"] or "UNDETERMINED — candidate for `freeze`"
        print(f"{r['da']:12} {r['lodged'] or '':10}  {state[:32]:32}  {r['address']}\n"
              f"{'':12} {r['description'][:110]}")
    return 0


def cmd_fetch(args) -> int:
    asyncio.run(fetch(args.da))
    data = load_cases()
    for number in args.da:
        if not (CACHE / number.replace("/", "-") / "detail.txt").exists():
            continue
        facts = council_facts(number)
        print(json.dumps({number: facts}, indent=2))
        if args.update:
            case = data["cases"].setdefault(number, {
                "address": None, "inputs": {},
                "input_notes": "TODO: write inputs from what the applicant knew at lodgement",
            })
            case["council"] = {k: v for k, v in facts.items() if k != "description"}
            case["council"]["fetched"] = date.today().isoformat()
            case.setdefault("description", facts.get("description"))
    if args.update:
        save_cases(data)
        print(f"\nUpdated {CASES_FILE.relative_to(ROOT)}.")
    return 0


def cmd_grade(args) -> int:
    data = load_cases()
    todo = {k: v for k, v in data["cases"].items()
            if (not args.da or k in args.da) and v.get("inputs") and v.get("address")}
    results, grades = {}, {}
    for number, case in todo.items():
        tool = asyncio.run(run_tools(case))
        results[number] = tool
        council = case.get("council") or {}
        if council.get("determination"):
            grades[number] = grade(council, tool)
            frozen = case.get("prediction")
            if frozen:
                grades[number]["prediction"] = "INFO — frozen " + frozen["frozen"] + ": " + \
                    "; ".join(f"{q} {v.split()[0]}" for q, v in grade(council, frozen["tool"]).items())
        print(f"{number:12} " + " | ".join(f"{q}: {v}" for q, v in grades.get(number, {}).items()),
              flush=True)

    lines = [f"# Tracker validation — {date.today().isoformat()}", "",
             f"{len(grades)} determined case(s) graded.", "", "```", _summary(grades), "```", ""]
    for number, g in grades.items():
        lines.append(f"## {number} — {data['cases'][number].get('description', '')[:90]}")
        lines += [f"- **{q}**: {v}" for q, v in g.items()] + [""]
    CACHE.mkdir(exist_ok=True)
    report = CACHE / f"report-{date.today().isoformat()}.md"
    report.write_text("\n".join(lines))
    (CACHE / f"results-{date.today().isoformat()}.json").write_text(json.dumps(results, indent=1))
    print("\n" + _summary(grades) + f"\n\nReport: {report.relative_to(ROOT)}")
    return 0


def cmd_freeze(args) -> int:
    data = load_cases()
    for number in args.da:
        case = data["cases"].get(number)
        if not case or not case.get("inputs"):
            print(f"{number}: no case with inputs — add one first", file=sys.stderr)
            continue
        if (case.get("council") or {}).get("determination") and not args.force:
            print(f"{number}: already determined — a prediction now has hindsight. "
                  "Use --force only if you know why.", file=sys.stderr)
            continue
        case["prediction"] = {"frozen": date.today().isoformat(),
                              "tool": asyncio.run(run_tools(case))}
        print(f"{number}: frozen", json.dumps(case["prediction"]["tool"]))
    save_cases(data)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    h = sub.add_parser("harvest")
    h.add_argument("--since", default="2024-07-01",
                   help="Lodged on or after (default: the current contributions plan's start)")
    h.add_argument("--streets", nargs="*")
    f = sub.add_parser("fetch")
    f.add_argument("da", nargs="+")
    f.add_argument("--update", action="store_true", help="record Council's figures in the case file")
    g = sub.add_parser("grade")
    g.add_argument("da", nargs="*")
    z = sub.add_parser("freeze")
    z.add_argument("da", nargs="+")
    z.add_argument("--force", action="store_true")
    args = parser.parse_args()
    return {"harvest": cmd_harvest, "fetch": cmd_fetch,
            "grade": cmd_grade, "freeze": cmd_freeze}[args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
