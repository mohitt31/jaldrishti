"""Score answers against the frozen benchmark (rules in benchmark/EVALUATION_CONTRACT.md)."""
from __future__ import annotations
import csv, json, pathlib
from .index import ROOT, docs

def load_bench(bench="original"):
    if bench not in ("original", "holdout"):
        raise ValueError("Unknown benchmark")
    base, prefix = (ROOT / "benchmark/holdout", "holdout") if bench == "holdout" else (ROOT / "benchmark", "jaldrishti")
    facts = {f["fact_id"]: f for f in csv.DictReader(open(base / f"{prefix}_facts.csv", encoding="utf-8"))}
    qs = list(csv.DictReader(open(base / f"{prefix}_questions.csv", encoding="utf-8")))
    return facts, qs

def _num(x):
    try: return float(str(x).replace(",", ""))
    except ValueError: return None

import re as _re
def _toks(s): return [t for t in _re.findall(r"[\w.]+", _re.sub(r"(?<=\d),(?=\d{3})", "", (s or "").lower())) if t]

def item_matches(item: dict, fact: dict, strict: bool = False) -> bool:
    """Same value, and either the gold document+page, or (non-strict) another copy whose cited page prints the gold row."""
    v1, v2 = _num(item["value"]), _num(fact["value"])
    if v1 is None or v2 is None or abs(v1 - v2) > 1e-9: return False
    if item.get("url") == fact["source_url"]:
        return not fact["pdf_page_number"] or str(item.get("page")) == str(fact["pdf_page_number"])
    if strict or not item.get("page"): return False
    from .verify import page_text
    from .index import docs
    meta = next((d for d in docs() if d["id"] == item["doc"]), None) or _disc(item["doc"])
    if not meta: return False
    pt = " ".join(_toks(page_text(meta["file"], int(item["page"]))))
    return all(t in pt for t in _toks(fact["exact_quote"]))

def _disc(doc_id):
    f = ROOT / "cache/discovered.json"
    if not f.exists(): return None
    return next((m for m in json.loads(f.read_text()).values() if m.get("id") == doc_id), None)

def score_one(q: dict, r: dict, facts: dict) -> dict:
    exp = q["expected_answer_type"]
    sup = [facts[f] for f in q["supporting_fact_ids"].split(";") if f]
    items = r.get("items", [])
    type_ok = r["answer_type"] == exp
    supported = [i for i in items if any(item_matches(i, f) for f in sup)]
    unsupported = len(items) - len(supported) if exp == "number_with_source" else 0
    covered = all(any(item_matches(i, f) for i in items) for f in sup)
    strict = all(any(item_matches(i, f, strict=True) for i in items) for f in sup)
    if exp == "number_with_source": correct = type_ok and covered and unsupported == 0
    elif exp == "not_comparable": correct = type_ok
    else: correct = type_ok and not items
    return {"id": q["question_id"], "expected": exp, "got": r["answer_type"], "correct": correct,
            "verified_items": sum(1 for i in items if i.get("page_verified")),
            "evidence_ok": covered if sup else None, "gold_doc_exact": strict if sup else None, "n_items": len(items), "unsupported": unsupported}

def summarise(rows: list[dict]) -> dict:
    n = len(rows)
    num = [r for r in rows if r["expected"] == "number_with_source"]
    abst_pred = [r for r in rows if r["got"] in ("insufficient_evidence", "not_comparable")]
    abst_true = [r for r in rows if r["expected"] in ("insufficient_evidence", "not_comparable")]
    tp = [r for r in abst_pred if r["got"] == r["expected"]]
    items = sum(r["n_items"] for r in num)
    answered = [r for r in rows if r["got"] in ("number_with_source", "not_comparable", "comparable")]
    wrong_answered = [r for r in answered if not r["correct"]]
    cited = sum(r["n_items"] for r in rows)
    verified = sum(r.get("verified_items", 0) for r in rows)
    gold_needed = [r for r in num if r.get("evidence_ok") is not None]
    return {"n": n, "accuracy": sum(r["correct"] for r in rows) / n if n else 0,
            "numeric_accuracy": sum(r["correct"] for r in num) / len(num) if num else None,
            "unsupported_items": sum(r["unsupported"] for r in num), "numeric_items": items,
            "gold_doc_exact_numeric": sum(1 for r in num if r.get("correct") and r.get("gold_doc_exact")),
            "page_verified_items": sum(r.get("verified_items", 0) for r in num),
            "abstention_precision": len(tp) / len(abst_pred) if abst_pred else None,
            "abstention_recall": len(tp) / len(abst_true) if abst_true else None,
            # selective QA (Kamath et al. 2020): how often it commits, and how often a committed answer is wrong
            "coverage": len(answered) / n if n else 0, "risk": len(wrong_answered) / len(answered) if answered else 0.0,
            # ALCE-style (Gao et al. 2023): cited numbers re-found on the cited page / gold facts recovered
            "citation_precision": verified / cited if cited else None,
            "citation_recall": sum(1 for r in gold_needed if r["evidence_ok"]) / len(gold_needed) if gold_needed else None}
