"""Parse a question into a grounded query: only places that exist in the corpus count."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from .gazetteer import norm, compact, find_districts, find_contaminant

MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                       "august", "september", "october", "november", "december"], 1)}
STOP = set("""a an the of in on at for to and or is are was were be by with from what which how many much
does do did can could this that these those its it as use only frozen corpus value values reported listed
report table recorded give given district well wells dug sample samples study""".split())

@dataclass
class Mention:
    text: str
    places: list[str] = field(default_factory=list)
    well_ids: list[str] = field(default_factory=list)
    unresolved_places: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)       # ISO yyyy-mm-dd or yyyy-mm
    years: list[str] = field(default_factory=list)
    statistics: list = field(default_factory=list)
    attribute: str | None = None
    tokens: set = field(default_factory=set)

@dataclass
class Query:
    text: str
    contaminant: str | None
    districts: list[str]
    intent: str                     # lookup | compare
    claim: str | None
    mentions: list[Mention]

def _dates(q: str):
    out = []
    for day, month, year in re.findall(r"\b(\d{1,2})[-/](\d{1,2})[-/]((?:19|20)\d\d)\b", q):
        from datetime import date
        try: out.append(date(int(year), int(month), int(day)).isoformat())
        except ValueError: pass
    for d, m, y in re.findall(r"\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+((?:19|20)\d\d)", q, re.I):
        out.append(f"{y}-{MONTHS[m.lower()]:02d}-{int(d):02d}")
    for m, y in re.findall(r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s+((?:19|20)\d\d)\b", q, re.I):
        k = next(v for n, v in MONTHS.items() if n.startswith(m.lower()[:3]))
        iso = f"{y}-{k:02d}"
        if not any(o.startswith(iso) for o in out): out.append(iso)
    for year in re.findall(r"\b(?:sampled|collected|measured)(?:\s+in)?\s+((?:19|20)\d\d)\b", q, re.I):
        if not any(x.startswith(year) for x in out): out.append(year)
    for year in re.findall(r"\bin\s+((?:19|20)\d\d)\s*[?.]?\s*$", q, re.I):
        if not any(x.startswith(year) for x in out): out.append(year)
    return out

def _statistics(q: str) -> list[str]:
    t, out = norm(q), []
    if re.search(r"population[- ]weighted", t): return ["population_weighted_mean"]
    if re.search(r"\bhighest\b|\bmaximum\b|\bmax\b|upper endpoint", t): out.append("max")
    if re.search(r"how many|number of|exceedance count|\bcount\b", t): out.append("count_exceeding")
    if re.search(r"\brange\b", t): out.append("range")
    if re.search(r"\bmean\b|\baverage\b", t) and not re.search(r"averaged", t): out.append("mean")
    return out

def _attribute(q: str):
    t = norm(q)
    if "detection limit" in t: return "detection_limit"
    if re.search(r"(exact|which|what)\s+(calendar\s+)?date", t) and "sampling date" not in t: return "date"
    return None

class Linker:
    """Grounds place names and well ids in the corpus vocabulary."""
    def __init__(self, evidence: list[dict]):
        self.places, self.wells = {}, set()
        for e in evidence:
            for p in e["places"]:
                k = norm(p)
                if len(compact(k)) >= 4: self.places.setdefault(k, p)
            if e.get("well_id"): self.wells.add(compact(e["well_id"]))
        self._sorted = sorted(self.places, key=len, reverse=True)
    def mention(self, text: str) -> Mention:
        t = " " + norm(text) + " "
        m = Mention(text=text)
        for k in self._sorted:
            pat = r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])"
            if re.search(pat, t):
                m.places.append(k); t = re.sub(pat, " ", t)
        for w in re.findall(r"\b[A-Z]{2,5}_?\d{1,4}\b", text):
            m.well_ids.append(compact(w))  # unknown IDs remain mandatory constraints
        tn = norm(text)
        for s, pat in [("m-ii", r"\bm-ii\b"), ("dug well", r"\bdug[- ]well\b|\bdw\b"), ("tube well", r"\btube[- ]well\b|\btw\b"), ("hand pump", r"hand pump")]:
            if re.search(pat, tn): m.sources.append(s)
        from .query_helpers import proper_names
        authors = {norm(n) for n in re.findall(r"([A-Z][a-z]+) et al", text)}
        for candidate in proper_names(text):
            k = norm(candidate)
            if k not in authors and not find_districts(candidate) and not any(k == p or k in p or p in k for p in m.places):
                m.unresolved_places.append(candidate)
        m.dates = _dates(text)
        m.years = re.findall(r"\b(?:19|20)\d\d\b", text)
        m.statistics = _statistics(text)
        m.attribute = _attribute(text)
        m.tokens = {w for w in re.findall(r"[a-z0-9][a-z0-9.\-–]+", tn) if w not in STOP and len(w) > 2}
        return m

COMPARE_START = re.compile(r"^\s*(can|could|does|do|is|are|should)\b", re.I)
CLAIMS = [
    ("repeat", r"repeat(?:ed)? measurements?|same sampling point"),
    ("time_series", r"time series|before-and-after|before and after"),
    ("change_same_well", r"increase at the same well|change at the same well|at the same well"),
    ("district_change", r"change in .*district mean|fall in district mean|district mean fluoride|worsening .*trend|district trend"),
    ("same_quantity", r"conflicting estimates|same district mean|same quantity|same statistic"),
    ("average", r"averaged|average[d]? into"),
    ("change", r"establish|increase|decrease|fall|rise|trend|change"),
]

def _split(q: str):
    """Split a comparison into its two compared items."""
    body = re.split(r"\b(?:establish|be treated|be averaged|constitute|be compared|treated as|as conflicting)\b", q, maxsplit=1)[0]
    body = re.sub(r"^\s*(can|could|does|do|is|are|should)\s+(comparing\s+)?(the\s+)?", "", body, flags=re.I)
    parts = re.split(r"\s+(?:and|with|versus|vs\.?)\s+(?:the\s+)?", body, maxsplit=1)
    return parts if len(parts) == 2 else [body]

def parse(q: str, linker: Linker) -> Query:
    con, dists = find_contaminant(q), find_districts(q)
    if COMPARE_START.match(q) and re.search(r"establish|treated|constitute|averag|conflict|compar|time series|repeat", q, re.I):
        claim = next((c for c, pat in CLAIMS if re.search(pat, q, re.I)), "change")
        ms = [linker.mention(p) for p in _split(q)]
        if len(ms) == 2 and len(ms[0].places) >= 2 and not ms[1].places:   # "Saidpur and Gangedda values"
            ms = [linker.mention(p) for p in ms[0].places]
        # A trailing sampling period qualifies both operands, unless each has its own.
        dates = _dates(q)
        for m in ms:
            if not m.dates and len(dates) == 1 and re.search(r"values? (?:from|on|in)\b", q, re.I): m.dates = list(dates)
        # "Village sample count and habitation count" shares one explicit place.
        if len(ms) == 2 and ms[0].places and not ms[1].places and not ms[1].well_ids:
            if all("count_exceeding" in m.statistics for m in ms):
                ms[1].places = list(ms[0].places)
        return Query(q, con, dists, "compare", claim, ms)
    return Query(q, con, dists, "lookup", None, [linker.mention(q)])
