"""Score answers against the frozen benchmark (rules in benchmark/EVALUATION_CONTRACT.md)."""
from __future__ import annotations
import csv, json, pathlib
from .index import ROOT, docs

def load_bench():
    facts = {f["fact_id"]: f for f in csv.DictReader(open(ROOT / "benchmark/jaldrishti_facts.csv", encoding="utf-8"))}
    qs = list(csv.DictReader(open(ROOT / "benchmark/jaldrishti_questions.csv", encoding="utf-8")))
    return facts, qs

def _num(x):
    try: return float(str(x).replace(",", ""))
    except ValueError: return None

def item_matches(item: dict, fact: dict) -> bool:
    v1, v2 = _num(item["value"]), _num(fact["value"])
    if v1 is None or v2 is None or abs(v1 - v2) > 1e-9: return False
    if item.get("url") != fact["source_url"]: return False
    return not fact["pdf_page_number"] or str(item.get("page")) == str(fact["pdf_page_number"])

def score_one(q: dict, r: dict, facts: dict) -> dict:
    exp = q["expected_answer_type"]
    sup = [facts[f] for f in q["supporting_fact_ids"].split(";") if f]
    items = r.get("items", [])
    type_ok = r["answer_type"] == exp
    supported = [i for i in items if any(item_matches(i, f) for f in sup)]
    unsupported = len(items) - len(supported) if exp == "number_with_source" else 0
    covered = all(any(item_matches(i, f) for i in items) for f in sup)
    if exp == "number_with_source": correct = type_ok and covered and unsupported == 0
    elif exp == "not_comparable": correct = type_ok
    else: correct = type_ok and not items
    return {"id": q["question_id"], "expected": exp, "got": r["answer_type"], "correct": correct,
            "evidence_ok": covered if sup else None, "n_items": len(items), "unsupported": unsupported}

def summarise(rows: list[dict]) -> dict:
    n = len(rows)
    num = [r for r in rows if r["expected"] == "number_with_source"]
    abst_pred = [r for r in rows if r["got"] in ("insufficient_evidence", "not_comparable")]
    abst_true = [r for r in rows if r["expected"] in ("insufficient_evidence", "not_comparable")]
    tp = [r for r in abst_pred if r["got"] == r["expected"]]
    items = sum(r["n_items"] for r in num)
    return {"n": n, "accuracy": sum(r["correct"] for r in rows) / n if n else 0,
            "numeric_accuracy": sum(r["correct"] for r in num) / len(num) if num else None,
            "unsupported_items": sum(r["unsupported"] for r in num), "numeric_items": items,
            "abstention_precision": len(tp) / len(abst_pred) if abst_pred else None,
            "abstention_recall": len(tp) / len(abst_true) if abst_true else None}
