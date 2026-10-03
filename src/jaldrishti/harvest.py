"""Build a cited evidence library for West Bengal with a fixed SerpApi budget.

Queries are generic templates over the districts where arsenic or fluoride in
groundwater is reported; they never use benchmark question text.
"""
from __future__ import annotations
import json, time
from .index import ROOT
from .search import results, trusted, relevant, LiveSearchLimit

ARSENIC_DISTRICTS = ["Nadia", "North 24 Parganas", "South 24 Parganas", "Murshidabad", "Malda", "Hooghly", "Purba Bardhaman", "Howrah"]
FLUORIDE_DISTRICTS = ["Birbhum", "Bankura", "Purulia", "Dakshin Dinajpur", "Uttar Dinajpur"]
STATE = [
    {"engine": "google", "q": "ground water quality West Bengal CGWB report"},
    {"engine": "google", "q": "ground water year book West Bengal CGWB"},
    {"engine": "google", "q": "annual ground water quality report CGWB arsenic fluoride"},
    {"engine": "google", "q": "arsenic fluoride drinking water West Bengal assessment report"},
]
LIBRARY = ROOT / "cache" / "library.json"

def queries():
    per = []
    for d in ARSENIC_DISTRICTS + FLUORIDE_DISTRICTS:
        c = "arsenic" if d in ARSENIC_DISTRICTS else "fluoride"
        per.append([{"engine": "google", "q": f"{c} groundwater {d} West Bengal CGWB report", "district": d},
                    {"engine": "google", "q": f"{d} district aquifer mapping groundwater report CGWB", "district": d},
                    {"engine": "google", "q": f"{c} groundwater {d} West Bengal report", "district": d},
                    {"engine": "google_scholar", "q": f"{c} groundwater {d} West Bengal", "district": d}])
    out = list(STATE)
    for k in range(4):                       # round-robin: every district gets template 1 before any gets template 2
        out += [p[k] for p in per]
    return out

def supplemental_queries():
    return [{"engine": "google", "q": "ground water year book West Bengal filetype:pdf"}] + [
        {"engine": "google", "q": f"aquifer mapping report {district} West Bengal filetype:pdf", "district": district}
        for district in ARSENIC_DISTRICTS + FLUORIDE_DISTRICTS]

def harvest(session, budget: int = 50, fetch_per_query: int = 4, supplement: bool = False) -> dict:
    lib = json.loads(LIBRARY.read_text()) if supplement and LIBRARY.exists() else {"queries": [], "docs": [], "credits": 0}
    previous = lib.get("credits", 0)
    lib.update({"built": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "budget": budget})
    credits, docs = 0, set(lib["docs"])
    for q in (supplemental_queries() if supplement else queries()):
        if credits >= budget: break
        params = {"engine": q["engine"], "q": q["q"]}
        try:
            d = session.api.search(**params)
        except LiveSearchLimit:
            lib["stopped_reason"] = "live request cap reached; partial harvest retained"
            break
        credits += 0 if d.get("_missing") else 1      # cached responses were paid for once: count them
        res = results(d); fetched, found = [], set()
        session.contaminant = None
        scope = [q["district"]] if q.get("district") else ["West Bengal"]
        for r in res:
            from .pipeline import nurl
            for u in (r["pdf"], r["link"]):
                if u and nurl(u) in session.by_url: found.add(session.by_url[nurl(u)])
        if q["engine"] == "google_scholar":
            from .fetch import pmid_for_title
            for r in res[:fetch_per_query]:
                try: pm = pmid_for_title(r["title"], offline=not session.live)
                except Exception: pm = None
                if pm:
                    did = f"pubmed_{pm}"
                    got = did if did in session.by_id else session._add(f"https://pubmed.ncbi.nlm.nih.gov/{pm}/", fetched)
                    if got: found.add(got)
        else:
            n = 0
            for r in res:
                u = r["pdf"]
                if not u or not trusted(u) or not relevant(r, None, scope or None): continue
                if n >= fetch_per_query: break
                n += 1
                from .pipeline import nurl
                got = session.by_url.get(nurl(u)) or session._add(u, fetched)
                if got: found.add(got)
        docs |= found
        lib["queries"].append({**q, "cached": d.get("_cached", False), "n_results": len(res), "found": sorted(found), "fetched": fetched})
        print(f"[{credits:>3}] {q['engine'][:7]} {q['q'][:70]:70s} found={sorted(found)}", flush=True)
        lib["docs"] = sorted(docs); lib["credits"] = previous + credits
        LIBRARY.write_text(json.dumps(lib, indent=1))
    lib["docs"] = sorted(docs); lib["credits"] = previous + credits
    LIBRARY.write_text(json.dumps(lib, indent=1))
    return lib
