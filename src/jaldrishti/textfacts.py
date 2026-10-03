"""Extract range / mean statements from abstract text, keeping only water-medium sentences."""
from __future__ import annotations
import re, xml.etree.ElementTree as ET
from .gazetteer import norm, find_districts, find_contaminant
from .units import detect_unit

NUMX = r"(\d+(?:\.\d+)?)"
UNIT = r"(µg\s*l\s*\(-1\)|µg\s*l-1|µg\s*/\s*l|μg\s*/\s*l|mg\s*/\s*l|mg\s*l\s*\(-1\)|mg\s*l-1|ppb|ppm)"
RANGE = [re.compile(rf"range[sd]?\s*(?:of|was|were|is|between|from|:)?\s*:?\s*{NUMX}\s*(?:-|–|to|and)\s*{NUMX}\s*{UNIT}", re.I),
         re.compile(rf"(?:varied|fluctuated|ranging|ranged)\s*(?:from|between)?\s*{NUMX}\s*(?:-|–|to|and)\s*{NUMX}\s*{UNIT}", re.I),
         re.compile(rf"\b{NUMX}\s*(?:to|-|–)\s*{NUMX}\s*{UNIT}", re.I)]
MEAN = re.compile(rf"mean\s*(?:±|\+/-)?\s*(?:s\.?\s*d\.?|sd)?\s*[:=(]?\s*{NUMX}\s*(?:±|\+/-)\s*{NUMX}\s*\)?\s*{UNIT}", re.I)
WATER = re.compile(r"water|groundwater|tube ?well|aquifer|hand ?pump|drinking", re.I)
BODY = re.compile(r"saliva|urin|hair|nail|serum|blood|plasma|skin|tissue", re.I)
OTHER = re.compile(r"\b(manganese|mn|chromium|cr|nickel|ni|lead|pb|iron|fe|zinc|zn|uranium|nitrate|barium|selenium)\b", re.I)

PLACE_STOP = set("""the a an this that these those in from of for to with and or as at by on during
west bengal india indian groundwater ground water drinking fluoride arsenic hydrogeochemical
hydrogeochemistry assessment sensitive health hazards hazard concentration concentrations
high low study studies samples sample ninety mean range regional modified optimal
monte carlo simulation bland altman friedman dean keywords introduction results conclusion
calcium magnesium sodium potassium chloride sulfate sulphate phosphate bicarbonate carbonate ca mg na cl fe mn zn cu as
abstract methods background objective environmental human population total besides notably
further dissolution geostatistical statistically significance journal copyright springer nature""".split())

def abstract_places(title: str, text: str) -> list[str]:
    """Conservative capitalisation heuristic; names remain study-level, not well locations."""
    from .gazetteer import DISTRICTS
    excluded = PLACE_STOP | {w for d, aliases in DISTRICTS.items()
                             for name in [d, *aliases] for w in norm(name).split()}
    names = []
    for match in re.finditer(r"\b[A-Z][a-z]+(?:[-'][A-Z]?[a-z]+)*\b", title + ". " + text):
        word = match.group(0)
        if norm(word) not in excluded and not OTHER.fullmatch(word) and word not in names:
            names.append(word)
    return names

def parse_pubmed(xml_bytes: bytes) -> dict:
    root = ET.fromstring(xml_bytes)
    art = root.find(".//Article")
    title = "".join(art.find("ArticleTitle").itertext()) if art is not None else ""
    abstract = " ".join("".join(a.itertext()) for a in root.findall(".//AbstractText"))
    authors = [a.findtext("LastName") for a in root.findall(".//Author") if a.findtext("LastName")]
    year = root.findtext(".//JournalIssue/PubDate/Year") or root.findtext(".//ArticleDate/Year")
    journal = root.findtext(".//Journal/Title")
    return {"title": title, "abstract": abstract, "authors": authors, "year": int(year) if year else None, "journal": journal}

def _clauses(text):
    for s in re.split(r"(?<=[.;])\s+(?=[A-Z(])", text):
        yield s

def text_evidence(doc: dict, text: str) -> list[dict]:
    out = []
    con_doc = find_contaminant(text)
    dists = find_districts(doc.get("title", "") + " " + text)
    period = re.search(r"(pre-?monsoon[^.;]{0,40}(?:19|20)\d\d|(?:19|20)\d\d\s*[-–]\s*(?:19|20)?\d\d)", text, re.I)
    for k, sent in enumerate(_clauses(text)):
        # split at commas/semicolons so 'water ..., saliva ...' are judged separately
        for part in re.split(r";|,\s+(?=(?:while|whereas|and)?\s*(?:in\s+)?(?:saliva|urine|hair|nail|serum|blood))", sent):
            if BODY.search(part) and (not WATER.search(part) or "urin" in part.lower()): continue
            if BODY.search(part) and WATER.search(part) and BODY.search(part).start() < WATER.search(part).start(): continue
            own = find_contaminant(part)
            if not own and OTHER.search(part): continue      # e.g. a manganese range in an arsenic paper
            con = own or con_doc
            for rx in RANGE:
                m = rx.search(part)
                if m:
                    lo, hi, u = m.group(1), m.group(2), detect_unit(m.group(3))
                    for st, v in (("range_min", lo), ("range_max", hi)):
                        out.append(_rec(doc, k, st, v, u, con, dists, period, part))
                    break
            m = MEAN.search(part)
            if m:
                out.append(_rec(doc, k, "mean", m.group(1), detect_unit(m.group(3)), con, dists, period, part, sd=m.group(2)))
    places = abstract_places(doc.get("title", ""), text)
    for record in out:
        record["places"] = places.copy()
    return out

def _rec(doc, k, st, v, unit, con, dists, period, sent, sd=None):
    return {"doc": doc["id"], "page": None, "table": None, "row": k, "col": st, "method": "abstract_text",
            "header_from": None, "contaminant": con, "statistic": st, "value_text": v, "value": float(v), "non_detect": False,
            "unit": unit, "threshold": None, "district": dists[0] if dists else None, "places": [], "source": None,
            "well_id": None, "date": None, "period": period.group(0) if period else None, "period_quote": sent,
            "spatial_support": "study", "context": doc.get("title", ""), "header": "abstract", "row_text": sent.strip(),
            "bbox": None, "publication_year": doc.get("year"), "sd": sd, "id": f"{doc['id']}:s{k}:{st}"}
