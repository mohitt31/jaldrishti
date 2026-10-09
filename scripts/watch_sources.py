"""Weekly source watch: a few SerpApi searches for new West Bengal groundwater-quality reports.

Lists trusted, relevant PDF results that are not yet in the library or the discovered-source cache.
It never downloads, indexes or answers anything: a human decides what to add.
Runs only when SERPAPI_KEY is set (GitHub Actions secret); otherwise it exits quietly.
"""
from __future__ import annotations
import json, os, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from jaldrishti.search import results, trusted, relevant          # noqa: E402
from jaldrishti.pipeline import nurl                                # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
QUERIES = [
    "ground water quality West Bengal CGWB report",
    "arsenic groundwater West Bengal CGWB report",
    "fluoride groundwater West Bengal CGWB report",
]

def known_urls() -> set:
    urls = set()
    for f in (ROOT / "corpus/docs.json",):
        if f.exists(): urls |= {nurl(d.get("url", "")) for d in json.loads(f.read_text())}
    f = ROOT / "cache/discovered.json"
    if f.exists(): urls |= {nurl(u) for u in json.loads(f.read_text())}
    return urls

def new_candidates(responses: list[dict], known: set) -> list[dict]:
    seen, out = set(known), []
    for q, d in responses:
        for r in results(d):
            u = r.get("pdf")
            if not u or not trusted(u) or not relevant(r, None, ["West Bengal"]): continue
            k = nurl(u)
            if k in seen: continue
            seen.add(k)
            out.append({"query": q, "rank": r["rank"], "title": r["title"], "url": u, "domain": r["domain"]})
    return out

def main() -> int:
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        print("SERPAPI_KEY not set: skipping source watch."); return 0
    import requests
    responses, credits = [], 0
    for q in QUERIES:
        r = requests.get("https://serpapi.com/search.json", params={"engine": "google", "q": q, "gl": "in", "hl": "en", "api_key": key}, timeout=90)
        r.raise_for_status(); responses.append((q, r.json())); credits += 1
    cands = new_candidates(responses, known_urls())
    out = ROOT / "reports/watch"; out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    report = {"date": stamp, "queries": QUERIES, "credits": credits, "new_candidates": cands}
    (out / "latest.json").write_text(json.dumps(report, indent=1))
    lines = [f"# Source watch, {stamp}", "", f"{credits} SerpApi searches. {len(cands)} trusted PDF result(s) not yet in the library.",
             "These are candidates for human review, not added sources.", ""]
    lines += [f"- [{c['title']}]({c['url']}) ({c['domain']}, rank {c['rank']} for \"{c['query']}\")" for c in cands] or ["- none"]
    (out / "LATEST.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines)); return 0

if __name__ == "__main__":
    sys.exit(main())
