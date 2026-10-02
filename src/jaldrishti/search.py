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
        r = requests.get(ENDPOINT, params={**params, "api_key": key}, timeout=60)
        r.raise_for_status()
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

# ---------- planner ----------
HINTS = {
    "cgwb": r"\bcgwb\b|central ground ?water|special drive|year ?book|naquim|aquifer mapping|annual ground water quality",
    "adb": r"\badb\b|asian development bank|imis",
    "scholar": r"\bet al\b|\bpaper\b|\bstudy\b|journal",
}

def plan(query, linker_places: list[str]) -> list[dict]:
    """Ordered query ladder. Level 0 is the fixed baseline query."""
    con = query.contaminant or "arsenic fluoride"
    dist = " ".join(query.districts) or "West Bengal"
    t = norm(query.text)
    years = " ".join(sorted(set(re.findall(r"\b(?:19|20)\d\d\b", query.text)))[:2])
    ladder = [{"level": 0, "why": "fixed baseline", "engine": "google", "q": f"{con} groundwater {dist} West Bengal"}]
    authors = re.findall(r"\b([A-Z][a-z]+) et al\b", query.text)
    if authors or re.search(HINTS["scholar"], t) and not re.search(HINTS["cgwb"] + "|" + HINTS["adb"], t):
        ladder.append({"level": 1, "why": "named study: scholarly index", "engine": "google_scholar",
                       "q": f"{' '.join(authors)} {con} {dist} {years}".strip()})
    if re.search(HINTS["adb"], t):
        ladder.append({"level": 1, "why": "source hint: ADB/IMIS", "engine": "google", "q": f"ADB {con} drinking water West Bengal {dist} filetype:pdf"})
    if re.search(HINTS["cgwb"], t) or not authors:
        kind = "special drive year book" if "special drive" in t else "aquifer mapping NAQUIM" if re.search(r"naquim|aquifer mapping", t) else "ground water quality"
        ladder.append({"level": 2, "why": "official report on the agency site", "engine": "google",
                       "q": f"site:cgwb.gov.in {con} {dist if 'naquim' in kind else 'West Bengal'} {kind} {years} filetype:pdf".replace("  ", " ")})
    if linker_places:
        ladder.append({"level": 3, "why": "place-level alias search", "engine": "google",
                       "q": f"\"{linker_places[0]}\" {con} {dist} groundwater"})
    return ladder
