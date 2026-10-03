"""SerpApi client with a response cache, a credit ledger and a query planner.

Every response is cached under cache/serpapi/<sha>.json, keyed by the request
parameters (never the key), so a frozen run is reproducible without an API key.
"""
from __future__ import annotations
import hashlib, json, os, pathlib, re, time
from urllib.parse import urlparse
from .index import ROOT
from .gazetteer import norm

CACHE = ROOT / "cache" / "serpapi"
LEDGER = ROOT / "cache" / "credits.jsonl"
ENDPOINT = "https://serpapi.com/search.json"
TRUSTED = ("gov.in", "nic.in", "adb.org", "worldbank.org", "who.int", "unicef.org", "ncbi.nlm.nih.gov",
           "sciencedirect.com", "springer.com", "wiley.com", "tandfonline.com", "mdpi.com", "nature.com")

class LiveSearchLimit(RuntimeError):
    """The caller's explicit live-request cap has been reached."""

def api_key():
    k = os.environ.get("SERPAPI_KEY")
    if k: return k
    env = ROOT / ".env"
    if env.exists():
        for l in env.read_text().splitlines():
            if l.startswith("SERPAPI_KEY="): return l.split("=", 1)[1].strip()
    return None

class SerpApi:
    def __init__(self, offline: bool = False):
        self.offline = offline
        self.live_attempts = 0
        self.max_live_searches = int(os.environ["SERPAPI_MAX_LIVE_SEARCHES"]) if "SERPAPI_MAX_LIVE_SEARCHES" in os.environ else None
        CACHE.mkdir(parents=True, exist_ok=True)
    @staticmethod
    def key_of(params: dict) -> str:
        p = {k: v for k, v in sorted(params.items()) if k != "api_key"}
        return hashlib.sha256(json.dumps(p, sort_keys=True).encode()).hexdigest()[:20]
    def search(self, **params) -> dict:
        params = {"hl": "en", "gl": "in", **params}
        f = CACHE / f"{self.key_of(params)}.json"
        if f.exists():
            d = json.loads(f.read_text()); d["_cached"] = True; return d
        if self.offline:
            return {"_cached": False, "_missing": True, "organic_results": []}
        import requests
        key = api_key()
        if not key: raise RuntimeError("SERPAPI_KEY not set (env or .env)")
        t = time.time()
        for attempt in range(3):
            if self.max_live_searches is not None and self.live_attempts >= self.max_live_searches:
                raise LiveSearchLimit("Session live-search limit reached; cached replay remains available")
            self.live_attempts += 1
            try:
                r = requests.get(ENDPOINT, params={**params, "api_key": key}, timeout=90)
                r.raise_for_status(); break
            except requests.RequestException:
                if attempt == 2: raise
                time.sleep(5 * (attempt + 1))
        d = r.json()
        d["_request"] = params
        f.write_text(json.dumps(d))
        with open(LEDGER, "a") as lg:
            lg.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "engine": params.get("engine"), "q": params.get("q"),
                                 "start": params.get("start", 0), "credits": 1, "seconds": round(time.time() - t, 2),
                                 "n": len(d.get("organic_results", []))}) + "\n")
        d["_cached"] = False
        return d

def results(d: dict) -> list[dict]:
    out = []
    for i, r in enumerate(d.get("organic_results", [])):
        link = r.get("link") or ""
        res = r.get("resources") or []
        pdf = next((x.get("link") for x in res if (x.get("file_format") or "").upper() == "PDF"), None)
        out.append({"rank": i + 1, "title": r.get("title", ""), "link": link, "pdf": pdf or (link if link.lower().split("?")[0].endswith(".pdf") else None),
                    "snippet": r.get("snippet", ""), "domain": urlparse(link).netloc,
                    "summary": (r.get("publication_info") or {}).get("summary", "")})
    return out

def trusted(url: str) -> bool:
    host = urlparse(url or "").netloc.lower()
    return any(host == t or host.endswith("." + t) for t in TRUSTED)

RELEVANT = re.compile(r"arsenic|fluoride|ground ?water|water quality|aquifer|hydrogeo|drinking water", re.I)

def relevant(r: dict, contaminant: str | None, scope: list[str] | None = None) -> bool:
    """Only fetch results about groundwater quality in the right area (saves bandwidth, avoids junk)."""
    t = f"{r['title']} {r['snippet']} {r['link']}"
    if not RELEVANT.search(t): return False
    if scope and not any(re.search(r"(?<![a-z])" + re.escape(x) + r"(?![a-z])", t, re.I) for x in scope + ["west bengal", "west-bengal", "eastern region", "GWYB ER"]):
        return False
    return not contaminant or re.search(contaminant + r"|ground ?water|water quality|aquifer", t, re.I) is not None

# ---------- planner ----------
SOURCE_HINTS = [  # phrase in question -> (query phrase, site restriction)
    (r"special drive", '"special drive" year book', "cgwb.gov.in"),
    (r"naquim|aquifer mapping", "aquifer mapping NAQUIM report", "cgwb.gov.in"),
    (r"annual ground water quality report", '"annual ground water quality report"', "cgwb.gov.in"),
    (r"\bcgwb\b|april 2022|shallow-aquifer", '"ground water quality" West Bengal', "cgwb.gov.in"),
    (r"\badb\b|imis", "ADB arsenic fluoride drinking water West Bengal", "adb.org"),
]

NOT_PLACE = set("""What Which How Can Could Does Do Is Are Use Only The April June July May March October Special Drive Annual Ground
Water Quality Report CGWB ADB IMIS NAQUIM Explain Retain Exclude Bengal West North South District Year Book Study Mondal Bhowmick
Table Dug Well Hand Pump India Mark Gaighata-only""".split())

def proper_names(text: str) -> list[str]:
    """Candidate place names from capitalisation alone (no corpus lookup, so search does not peek at the answer)."""
    from .gazetteer import find_districts
    toks = re.findall(r"[A-Z][a-zA-Z]+(?:\([A-Za-z]+\))?|[a-z]+|\S", text)
    out, cur = [], []
    for i, tk in enumerate(toks):
        if re.match(r"^[A-Z][a-z]", tk) and tk not in NOT_PLACE and i > 0 and not find_districts(tk):
            cur.append(tk)
        else:
            if cur: out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    return [o for o in out if len(o) > 3 and not re.search(r"et$", o)]

def plan(query, places: list[str] | None = None) -> list[dict]:
    """Ordered query ladder (level 0 = the question itself, which is also the baseline)."""
    con = query.contaminant or ""
    dist = " ".join(query.districts) if len(query.districts) < 2 else "(" + " OR ".join(query.districts) + ")"
    t = norm(query.text)
    years = " ".join(dict.fromkeys(re.findall(r"\b(?:19|20)\d\d\b", query.text)))
    steps = []
    authors = re.findall(r"\b([A-Z][a-z]+) et al\b", query.text)
    if authors:
        st = {"level": 1, "why": "named study -> Google Scholar", "engine": "google_scholar",
              "q": " ".join(f"{' '.join(authors)} {con} {'drinking water' if 'drinking' in t else 'groundwater'} West Bengal {dist}".split())}
        yrs = re.findall(r"\b(?:19|20)\d\d\b", query.text)
        if yrs: st |= {"as_ylo": min(yrs), "as_yhi": max(yrs)}
        steps.append(st)
    for pat, phrase, site in SOURCE_HINTS:
        if re.search(pat, t):
            steps.append({"level": 1, "why": f"source named in question -> {site}", "engine": "google",
                          "q": " ".join(f"{con} {dist} {phrase}".split()), "as_sitesearch": site})
            break
    places = proper_names(query.text)
    for p in places[:2]:
        steps.append({"level": 2, "why": "place-level search", "engine": "google", "q": " ".join(f'"{p}" {con or "water quality"} groundwater {dist}'.split())})
    if not authors and not any(s["engine"] == "google" and s.get("as_sitesearch") for s in steps):
        steps.append({"level": 3, "why": "state report fallback", "engine": "google",
                      "q": " ".join(f"{con} {dist} groundwater quality report West Bengal".split()), "as_sitesearch": "cgwb.gov.in"})
    if not authors and re.search(r"\bstudy\b|paper|journal", t):
        steps.append({"level": 3, "why": "research fallback", "engine": "google_scholar", "q": f"{con} groundwater {dist} West Bengal {years}".strip()})
    return steps

def resolve_district_step(place: str) -> dict:
    return {"level": 0, "why": f"resolve district of '{place}'", "engine": "google", "q": f"{place} West Bengal district", "resolve": place}

def district_from_results(d: dict) -> str | None:
    """Vote over knowledge graph + snippets for the district a place belongs to."""
    from .gazetteer import find_districts
    texts = []
    kg = d.get("knowledge_graph") or {}
    texts += [kg.get("title", ""), kg.get("description", ""), kg.get("type", "")]
    for r in d.get("organic_results", [])[:6]:
        texts += [r.get("title", ""), r.get("snippet", "")]
    votes = {}
    for i, tx in enumerate(texts):
        for dd in find_districts(tx)[:1]:
            votes[dd] = votes.get(dd, 0) + (3 if i < 3 else 1)
    if not votes: return None
    ranked = sorted(votes, key=votes.get, reverse=True)
    # a village name shared by two districts: keep both when the runner-up has real support
    return ranked[:2] if len(ranked) > 1 and votes[ranked[1]] >= 0.5 * votes[ranked[0]] else ranked[:1]

def baseline(query) -> dict:
    return {"level": 0, "why": "baseline: the question as typed", "engine": "google", "q": query.text}
