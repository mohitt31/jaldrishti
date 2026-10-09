"""Answer a question from indexed evidence, or abstain with a reason. Deterministic; no LLM."""
from __future__ import annotations
import re
from .gazetteer import norm, compact
from .question import Query, Mention, Linker, parse
from .units import to_mg_l, detect_unit

CONC_UNITS = {"mg/L", "µg/L", "ppb", "ppm"}
SRC_MAP = {"m-ii": {"m-ii"}, "dug well": {"dug well", "dw"}, "tube well": {"tube well", "tw"}, "hand pump": {"hand pump", "hp"}}

def _bound(p): return r"(?<![a-z0-9])" + re.escape(p) + r"(?![a-z0-9])"

def score(e: dict, m: Mention, q: Query, stat: str | None, meta: dict) -> float | None:
    if m.unresolved_places: return None
    if q.contaminant and e["contaminant"] != q.contaminant: return None
    if q.districts and e.get("district") not in q.districts: return None
    if e.get("non_detect"): return None
    # A named document family is a constraint, not a ranking bonus.
    full = norm(q.text)
    source = norm(" ".join([meta.get("title", ""), meta.get("period_text", ""), meta.get("url", "")]))
    for phrase in ("annual ground water quality report", "ground water quality of west bengal", "aquifer management plan", "ground water year book"):
        if phrase in full and phrase not in source: return None
    if re.search(r"\badb\b", full) and "adb" not in source: return None
    if "deeper" in norm(m.text) and e.get("aquifer") != "deeper": return None
    if "shallow" in norm(m.text) and e.get("aquifer") != "shallow": return None
    s = 0.0
    if e["statistic"] == "count_exceeding":
        entities = {"samples": r"\bsamples?\b", "blocks": r"\bblocks?\b",
                    "habitations": r"\bhabitations?\b", "wells": r"\bwells?\b"}
        requested = {name for name, pattern in entities.items() if re.search(pattern, norm(m.text))}
        requested_threshold = re.search(r"(?:above|exceed(?:ed|ing)?|>)\s*(\d+(?:\.\d+)?)", norm(m.text))
        if requested_threshold:
            wanted_unit, given_unit = detect_unit(m.text), detect_unit(e.get("header", ""))
            if wanted_unit not in CONC_UNITS or given_unit not in CONC_UNITS or e.get("threshold") is None: return None
            if abs(to_mg_l(float(requested_threshold.group(1)), wanted_unit) - to_mg_l(float(e["threshold"]), given_unit)) > 1e-12: return None
        entity = norm(e.get("entity") or e.get("unit") or "")
        entity = next((name for name, pattern in entities.items() if re.fullmatch(pattern, entity)), entity)
        if len(requested) == 1:
            if entity in entities and entity not in requested:
                return None
            if entity not in requested: return None
            s += 4
    pl = norm(" | ".join(e["places"]))
    hit = [p for p in m.places if re.search(_bound(p), pl)]
    if m.places and not hit: return None
    s += 3 * len(hit)
    if m.well_ids:
        if compact(e.get("well_id") or "") not in m.well_ids: return None
        s += 3
    if m.sources:
        if not any(norm(e.get("source") or "") in SRC_MAP[x] for x in m.sources): return None
        s += 1
    if e.get("spatial_support") == "site" and not m.places and not m.well_ids:
        return None
    if stat:
        want = {"range": {"min", "max", "range_min", "range_max"}, "min": {"min", "range_min"},
                "max": {"max", "range_max"}}.get(stat, {stat})
        if e["statistic"] not in want: return None
        s += 2
    elif not m.places and not m.well_ids:
        return None
    else:
        s += 1 if e["statistic"] == "single" else 0
    for d in m.dates:
        if e.get("date"):
            if not e["date"].startswith(d) and not d.startswith(e["date"]): return None
            s += 2
        elif e.get("period") and re.search(r"(19|20)\d\d", e["period"] or ""):
            y, mo = d[:4], d[5:7]
            per = norm(e["period"])
            mon = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"][int(mo) - 1] if mo else None
            years = {int(x) for x in re.findall(r"(?:19|20)\d\d", per)}
            span = re.search(r"((?:19|20)\d\d)\s*-\s*(\d\d)\b", per)
            if span: years |= set(range(int(span.group(1)), int(span.group(1)[:2] + span.group(2)) + 1))
            if int(y) not in years: return None          # question names a time the source does not cover
            if len(d) > 7: return None  # a period cannot substantiate a specific calendar day
            if mon and mon not in per: return None
            s += 2
        else:
            return None  # a requested sampling date needs evidence
    ctx = norm(" ".join([e.get("context", ""), e.get("header", ""), meta.get("title", ""), meta.get("publisher", ""), str(e.get("period") or "")]))
    s += min(3.0, 0.4 * sum(1 for tk in m.tokens if len(tk) > 3 and tk in ctx))
    if e.get("spatial_support") == "district" and re.search(r"\bdistrict\b", norm(m.text)): s += 0.5
    return s

def _cite(e, metas):
    m = metas.get(e["doc"], {})
    return {"value": e["value_text"], "unit": e["unit"], "statistic": e["statistic"], "place": ", ".join(e["places"][:3]) or e.get("district") or "",
            "contaminant": e.get("contaminant"), "location": e.get("location"), "aquifer": e.get("aquifer"), "period_basis": e.get("period_basis"),
            "district": e.get("district"), "source_type": e.get("source"), "well_id": e.get("well_id"), "date": e.get("date"),
            "period": e.get("period"), "period_quote": e.get("period_quote"), "threshold": e.get("threshold"), "spatial_support": e.get("spatial_support"),
            "doc": e["doc"], "title": m.get("title"), "url": m.get("url"), "page": e["page"], "quote": e["row_text"],
            "header": e.get("header"), "publication_year": m.get("year"), "evidence_id": e.get("id"), "bbox": e.get("bbox")}

def best(ev, m, q, stat, metas, k=1):
    sc = [(score(e, m, q, stat, metas.get(e["doc"], {})), e) for e in ev]
    sc = sorted([(s, e) for s, e in sc if s is not None], key=lambda t: -t[0])
    return sc[:k] if k else sc

AUTHOR = re.compile(r"\b([A-Z][a-z]+) et al\b")

def author_docs(text, metas):
    """Docs whose author list contains a surname named in the text (None = no author named)."""
    names = AUTHOR.findall(text)
    if not names: return None
    return {d for d, m in metas.items() if any(n.lower() in norm(" ".join(m.get("authors", []))) for n in names)}, names

def lookup(ev, q: Query, metas) -> dict:
    m = q.mentions[0]
    ad = author_docs(q.text, metas)
    if ad is not None:
        docs_ok, names = ad
        if not docs_ok:
            return {"answer_type": "insufficient_evidence", "items": [], "needs_source": names,
                    "reason": f"The question names {', '.join(n + ' et al.' for n in names)}, which is not in the corpus. Search recovery should look for it."}
        ev = [e for e in ev if e["doc"] in docs_ok]
    if m.statistics == ["population_weighted_mean"]:
        return {"answer_type": "insufficient_evidence", "reason": "No source in the corpus reports a population-weighted mean; computing one would need population data and a sampling design the sources do not give.", "items": []}
    items, missing = [], []
    stats = [s for s in m.statistics if s != "range"] or ([None] if "range" not in m.statistics else [])
    if "range" in m.statistics: stats += ["min", "max"]
    targets = [(p, s) for p in (m.places or [None]) for s in stats]
    for p, s in targets:
        mm = Mention(**{**m.__dict__, "places": [p] if p else []})
        r = best(ev, mm, q, s, metas)
        if r: items.append(_cite(r[0][1], metas) | {"score": round(r[0][0], 2), "asked": p or s})
        else: missing.append(p or s)
    if m.attribute == "date":
        undated = [i for i in items if not i["date"]]
        if items and undated:
            return {"answer_type": "insufficient_evidence", "items": [], "related": items,
                    "reason": f"The matching record gives only the period '{undated[0]['period']}', not a calendar date."}
    if m.attribute == "detection_limit":
        return {"answer_type": "insufficient_evidence", "items": [], "related": items,
                "reason": "The matching row reports a value but no detection limit for that result."}
    day = [d for d in m.dates if len(d) > 7]
    if not items and day:
        # a calendar day was asked; look for the same record at month precision and show it as context, not as the answer
        month = Mention(**{**m.__dict__, "dates": [d[:7] for d in m.dates]})
        related = []
        for p, s in targets:
            r = best(ev, Mention(**{**month.__dict__, "places": [p] if p else []}), q, s, metas)
            if r: related.append(_cite(r[0][1], metas) | {"score": round(r[0][0], 2), "asked": p or s})
        if related:
            i = related[0]
            return {"answer_type": "insufficient_evidence", "items": [], "related": related,
                    "reason": f"The source gives only the sampling period '{i['period']}', not the day {day[0]}. "
                              f"The {i['period']} record is shown as context: {i['value']} {i['unit'] or ''} at {i['place']}, page {i['page']}. "
                              f"It should not be reported as a {day[0]} measurement."}
    if not items:
        return {"answer_type": "insufficient_evidence", "items": [], "reason": "No record in the corpus matches " + ", ".join(str(x) for x in missing) + "."}
    out = {"answer_type": "number_with_source", "items": items}
    if missing:
        return {"answer_type": "insufficient_evidence", "items": [], "related": items,
                "reason": "No complete set of requested measurements was found; partial evidence is context only.", "missing": missing}
    return out

def _conc_mg(i):
    try: v = float(i["value"].replace(",", ""))
    except Exception: return None
    return to_mg_l(v, i["unit"]) if i["unit"] in CONC_UNITS else None

def compare(ev, q: Query, metas) -> dict:
    if len(q.mentions) != 2:
        return {"answer_type": "insufficient_evidence", "reason": "Could not identify two items to compare.", "items": []}
    its = []
    for m in q.mentions:
        ad = author_docs(m.text, metas)
        if ad is not None and not ad[0]:
            return {"answer_type": "insufficient_evidence", "items": [], "related": its, "needs_source": ad[1],
                    "reason": f"'{m.text.strip()}' cites {', '.join(ad[1])} et al., which is not in the corpus."}
        evm = [e for e in ev if e["doc"] in ad[0]] if ad else ev
        stats = [s for s in m.statistics if s in ("max", "mean", "count_exceeding")] or [None]
        r = best(evm, m, q, stats[0], metas)
        if not r: return {"answer_type": "insufficient_evidence", "items": [], "related": its, "reason": f"No record matches: '{m.text.strip()}'."}
        its.append(_cite(r[0][1], metas))
    a, b = its
    def point(i):
        return compact(i.get("well_id") or i.get("location") or (i["place"].split(", ")[-1] if i["place"] else ""))
    same_point = bool(point(a)) and point(a) == point(b) and a["district"] == b["district"] and \
        (a["source_type"] or "") == (b["source_type"] or "") and a["spatial_support"] == b["spatial_support"] == "site"
    fails = []
    def need(cond, msg):
        if not cond: fails.append(msg)
    pa, pb = (a["date"] or a["period"]), (b["date"] or b["period"])
    kind = lambda i: "concentration" if i["unit"] in CONC_UNITS else f"count of {i['unit']}" if i["statistic"].startswith("count") else i["unit"] or "unknown"
    stat_msg = f"different statistics: {a['statistic']} ({a['place']}) vs {b['statistic']} ({b['place']})"
    supp_msg = f"different spatial support: {a['spatial_support']} vs {b['spatial_support']}"
    c = q.claim
    if c in ("repeat", "time_series", "change_same_well", "change"):
        need(same_point, f"not the same sampling point: {a['place']} [{a['source_type'] or '-'}{' ' + a['well_id'] if a['well_id'] else ''}] vs {b['place']} [{b['source_type'] or '-'}{' ' + b['well_id'] if b['well_id'] else ''}]")
        need(a["statistic"] == b["statistic"], stat_msg)
        if c != "repeat": need(bool(pa and pb) and pa != pb, f"no time separation: both {pa}")
    if c in ("district_change", "same_quantity", "average"):
        need(a["statistic"] == b["statistic"], stat_msg)
        need(kind(a) == kind(b), f"different quantities: {kind(a)} vs {kind(b)}")
    if c in ("district_change", "same_quantity"):
        need(a["spatial_support"] == b["spatial_support"] == "district", supp_msg if a["spatial_support"] != b["spatial_support"] else f"neither value is a district-wide {('mean' if 'mean' in norm(q.text) else 'estimate')}")
        if "mean" in norm(q.text): need(a["statistic"] == b["statistic"] == "mean", f"a district mean is claimed but the values are {a['statistic']} and {b['statistic']}")
    if c == "district_change":
        need(bool(pa and pb) and pa != pb, f"no time separation: both {pa}")
        if a["statistic"].startswith("count"): need(a["threshold"] == b["threshold"] and a["doc"] == b["doc"], "counts come from different programmes or thresholds")
    note = None
    ca, cb = _conc_mg(a), _conc_mg(b)
    if ca is not None and cb is not None:
        note = f"After unit conversion: {ca*1000:g} µg/L vs {cb*1000:g} µg/L."
    if fails:
        return {"answer_type": "not_comparable", "items": its, "reasons": fails, "note": note}
    return {"answer_type": "comparable", "items": its, "reasons": [], "note": note}

class Engine:
    def __init__(self, evidence: list[dict], metas: dict, verifier=None):
        self.ev, self.metas, self.linker = evidence, metas, Linker(evidence)
        self.verifier = verifier
    def ask(self, text: str) -> dict:
        from .locales import normalize_question
        normalized, language = normalize_question(text)
        q = parse(normalized, self.linker)
        unknown = re.findall(r"[\u0900-\u09ff]+", normalized)
        if unknown:
            r = {"answer_type": "insufficient_evidence", "items": [], "reason": "Unresolved words or village names: " + ", ".join(unknown) + ". Village names are preserved; try the source spelling in English."}
            if language:
                from .locales import HEADERS
                r.update(language=language, language_header=HEADERS[language], normalized_question=normalized)
            return r
        r = compare(self.ev, q, self.metas) if q.intent == "compare" else lookup(self.ev, q, self.metas)
        verify_item = self.verifier
        if verify_item is None:
            from .verify import verify_item
        for key in ("items", "related"):
            for i in r.get(key, []):
                i["page_verified"] = verify_item(i, self.metas.get(i["doc"], {}))
                i["row_verified"] = bool(i["page_verified"] and i.get("bbox"))
                i["verification_scope"] = "row_number_and_explicit_identity" if i.get("bbox") else "page_number_presence"
        if r["answer_type"] in ("number_with_source", "not_comparable", "comparable"):
            bad = [i for i in r["items"] if not i["page_verified"]]
            r["items"] = [i for i in r["items"] if i["page_verified"]]
            if bad: r["dropped_unverified"] = [i["value"] for i in bad]
            if bad or not r["items"]:
                r = {"answer_type": "insufficient_evidence", "items": [], "reason": "Candidate evidence failed the page re-read check; no complete grounded answer is available."} | {"parsed": r.get("parsed")}
        r["parsed"] = {"intent": q.intent, "claim": q.claim, "contaminant": q.contaminant, "districts": q.districts,
                       "mentions": [{"text": m.text, "places": m.places, "well_ids": m.well_ids, "sources": m.sources,
                                     "dates": m.dates, "statistics": m.statistics, "attribute": m.attribute} for m in q.mentions]}
        if language:
            from .locales import HEADERS
            r["language"] = language
            r["language_header"] = HEADERS[language]
            r["normalized_question"] = normalized
        return r
