"""Turn tables into typed evidence records (one per measured cell)."""
from __future__ import annotations
import re
from .gazetteer import norm, find_districts, find_contaminant
from .units import detect_unit
from .tables import Table, is_num, ND

MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
PERIOD_RES = [
    re.compile(rf"\b(?:{MONTHS})[a-z]*\.?,?\s*(?:19|20)\d\d\b", re.I),
    re.compile(r"\b(?:19|20)\d\d\s*[-–]\s*(?:(?:19|20)\d\d|\d\d)\b"),
]
DATE_RE = re.compile(r"^(\d{1,2})\s*[-./]\s*(\d{1,2})\s*[-./]\s*((?:19|20)\d\d)$")
WELL_ID = re.compile(r"^[A-Z]{2,5}\s*[A-Z]?\s*_?\s*\d{1,4}$")
SOURCES = ["dug well", "tube well", "hand pump", "deep hp", "dw", "tw", "hp", "m-ii", "bw", "pz"]

def _analyte_of(h: str) -> str | None:
    t = norm(h)
    if re.match(r"^(f|f-|f−)(\s|\(|$)", t) or "fluoride" in t: return "fluoride"
    if re.match(r"^as(\s|\(|$)", t) or "arsenic" in t: return "arsenic"
    return None

def column_role(header: str, caption: str) -> dict | None:
    t = norm(header)
    if not t: return None
    if not _analyte_of(header):
        if re.match(r"^max", t): return {"role": "stat", "statistic": "max"}
        if re.match(r"^min", t): return {"role": "stat", "statistic": "min"}
        if "exceed" in t and "permissible" in t: return {"role": "stat", "statistic": "pct_exceeding_permissible"}
        if "exceed" in t and "acceptable" in t: return {"role": "stat", "statistic": "pct_exceeding_acceptable"}
    an = _analyte_of(header) or (find_contaminant(caption) if re.search(r"\b(as|f)\b|arsenic|fluoride|conc", t) else None)
    thr = re.search(r">\s*(\d+(?:\.\d+)?)", t)
    if "date" in t: return {"role": "date"}
    if "%" in t or "percent" in t:
        return {"role": "measure", "statistic": "pct_exceeding" if (thr or "exceed" in t) else "percent", "contaminant": an,
                "threshold": thr.group(1) if thr else None, "entity": "samples"} if an or thr else None
    if re.search(r"\b(no|no\.|number)\b", t) and (thr or "exceed" in t or "having" in t or "affected" in t):
        ent = "habitations" if "habitation" in t else "blocks" if "block" in t else "samples"
        return {"role": "measure", "statistic": "count_exceeding", "contaminant": an, "threshold": thr.group(1) if thr else None, "entity": ent}
    if "habitation" in t and thr:
        return {"role": "measure", "statistic": "count_exceeding", "contaminant": an, "threshold": thr.group(1), "entity": "habitations"}
    if re.search(r"tested|analysed|analyzed|total no", t):
        return {"role": "measure", "statistic": "count_total", "contaminant": an, "entity": "samples"}
    if an and (_analyte_of(header) or re.search(r"highest|max|conc", t)):
        st = "max" if re.search(r"highest|max", t) else "min" if "min" in t else "mean" if re.search(r"mean|average", t) else "single"
        return {"role": "measure", "statistic": st, "contaminant": an, "unit": detect_unit(header)}
    if re.match(r"^max", t): return {"role": "stat", "statistic": "max"}
    if re.match(r"^min", t): return {"role": "stat", "statistic": "min"}
    if "exceed" in t and "permissible" in t: return {"role": "stat", "statistic": "pct_exceeding_permissible"}
    if "exceed" in t and "acceptable" in t: return {"role": "stat", "statistic": "pct_exceeding_acceptable"}
    return None

def _period(*texts):
    for tx in texts:
        for rx in PERIOD_RES:
            m = rx.search(tx or "")
            if m: return m.group(0), tx
    return None, None

def _date(cell):
    m = DATE_RE.match(re.sub(r"\s+", "", cell or "").replace("-", "-"))
    if m: return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return None

def _value(cell):
    c = (cell or "").strip()
    if norm(c) in ND: return None, True
    if not is_num(c): return None, False
    try: return float(c.replace(",", "").replace("%", "").lstrip("<>").strip()), False
    except ValueError: return None, False

_DCOMPACT = None
def _places(texts, src):
    global _DCOMPACT
    from .gazetteer import DISTRICTS, compact
    if _DCOMPACT is None:
        _DCOMPACT = {compact(d) for d in DISTRICTS} | {compact(a) for v in DISTRICTS.values() for a in v} | {"westbengal", "naquim", "cgwb"}
    out = []
    for p in texts:
        c = compact(p)
        if p == src or c in _DCOMPACT or _date(p) or WELL_ID.match(p.strip()) or norm(p) in SOURCES or len(c) < 3 or _analyte_of(p):
            continue
        out.append(p)
    return out

def table_evidence(t: Table, doc_meta: dict, page_text: str = "") -> list[dict]:
    out = []
    cap = " | ".join([t.caption, t.note])
    hdr_text = " ".join(t.columns)
    table_unit = detect_unit(hdr_text) or detect_unit(t.caption)
    roles = [column_role(h, t.caption) for h in t.columns]
    for j in range(1, len(roles)):          # empty header inherits the spanning header on its left
        if not t.columns[j] and roles[j] is None and roles[j - 1] and (j < 2 or t.columns[j - 1]):
            roles[j] = roles[j - 1]
    default_d = find_districts(t.caption) or doc_meta.get("districts") or []
    per_tbl, per_q = _period(t.caption, t.note, doc_meta.get("period_text", ""), page_text[:600])
    transposed = any(r and r["role"] == "stat" for r in roles)
    for ri, row in enumerate(t.rows):
        texts = [c for c in row if c and not is_num(c) and norm(c) not in ND]
        if not texts and not transposed: continue
        date = next((d for d in (_date(c) for c in row) if d), None)
        well = next((re.sub(r"\s+", "", c) for c in row if WELL_ID.match(c.strip())), None)
        src = next((c for c in texts if norm(c) in SOURCES), None)
        dists = find_districts(" ".join(texts)) or default_d
        rowtxt = " | ".join(c for c in row if c)
        label = next((c for c in row if c and not is_num(c)), "")
        row_an = _analyte_of(label) if transposed else None
        for ci, cell in enumerate(row):
            r = roles[ci] if ci < len(roles) else None
            if not r or r["role"] not in ("measure", "stat"): continue
            if r["role"] == "stat" and not row_an: continue
            val, nd = _value(cell)
            if val is None and not nd: continue
            an = r.get("contaminant") if r["role"] == "measure" else row_an
            if not an: continue
            unit = r.get("unit") if r["role"] == "measure" else None
            if r["role"] == "stat": unit = None if r["statistic"].startswith("pct") else (detect_unit(row[0]) or table_unit)
            elif r["statistic"] in ("count_exceeding", "count_total"): unit = r.get("entity")
            elif r["statistic"] in ("pct_exceeding", "percent"): unit = "%"
            else: unit = unit or table_unit
            out.append({
                "doc": t.doc, "page": t.page, "table": t.idx, "row": ri, "col": ci, "method": t.method,
                "header_from": t.header_from, "contaminant": an, "statistic": r["statistic"],
                "value_text": cell.strip(), "value": val, "non_detect": nd, "unit": unit,
                "threshold": r.get("threshold"), "district": dists[0] if len(dists) == 1 else (dists[0] if dists else None),
                "places": _places(texts, src),
                "source": src, "well_id": well, "date": date,
                "period": date or per_tbl, "period_quote": per_q if not date else rowtxt,
                "spatial_support": "district" if not [p for p in texts if not find_districts(p) and not _analyte_of(p) and norm(p) not in SOURCES and not WELL_ID.match(p)] else "site",
                "context": cap, "header": t.columns[ci] if ci < len(t.columns) else "", "row_text": rowtxt,
                "bbox": list(t.row_bboxes[ri]) if ri < len(t.row_bboxes) else None,
                "publication_year": doc_meta.get("year"),
            })
    return out
