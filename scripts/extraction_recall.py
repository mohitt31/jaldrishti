"""How many gold table facts does the automatic index recover (same doc, page, value, place)?"""
import csv, sys, json
sys.path.insert(0, "src")
from jaldrishti.index import load, docs
from jaldrishti.gazetteer import compact
by_url = {d["url"]: d["id"] for d in docs()}
ev = load()
ok, miss = 0, []
for f in csv.DictReader(open("benchmark/jaldrishti_facts.csv", encoding="utf-8")):
    did = by_url.get(f["source_url"])
    if not did: continue
    v = float(f["value"]); place = compact(f["block_or_village"].split(" and ")[0]) if f["block_or_village"] else compact(f["district"])
    hit = [e for e in ev if e["doc"] == did and e["page"] == int(f["pdf_page_number"]) and e["value"] is not None
           and abs(e["value"] - v) < 1e-9 and e["contaminant"] == f["contaminant"]
           and (place in compact(e["row_text"]) or (not f["block_or_village"] and e.get("district") == f["district"]))]
    if hit: ok += 1
    else: miss.append((f["fact_id"], did, f["pdf_page_number"], f["value"], f["block_or_village"] or f["district"]))
print(f"recovered {ok}/{ok+len(miss)}")
for m in miss: print("MISS", m)
