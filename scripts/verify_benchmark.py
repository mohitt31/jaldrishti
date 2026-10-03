"""Check each benchmark fact against the text of its cited PDF page.
Statuses: EXACT (value + quote on cited page), VALUE_ONLY, OFFSET (found on a
nearby page), NOT_FOUND, EXTERNAL (source not in local corpus)."""
import csv, re, subprocess, json, sys, pathlib
FILES = {"1687515522384483915": "yearbook_2015_16.pdf", "170799987922095186": "gwq_west_bengal.pdf",
         "1762854375262680475": "annual_gwq_2025.pdf", "16905335181706431115": "naquim_bankura.pdf",
         "1744936456830985840": "amp_purulia.pdf", "49107-006-sd-01": "adb_49107-006-sd-01.pdf"}
C = pathlib.Path("corpus"); cache = {}
def page(pdf, n):
    k = (pdf, n)
    if k not in cache:
        r = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), "-layout", str(C/pdf), "-"], capture_output=True, text=True)
        cache[k] = r.stdout if r.returncode == 0 else ""
    return cache[k]
norm = lambda s: re.sub(r"\s+", " ", re.sub(r"(?<=\d),(?=\d{3})", "", s).replace("\u2013", "-").replace("\u2212", "-")).strip().lower()
def has_value(txt, v):
    v = v.strip()
    try: float(v)
    except ValueError: return v.lower() in txt
    return re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", txt) is not None
def has_quote(txt, q):
    toks = [t for t in re.findall(r"[\w.]+", norm(q)) if t]
    return bool(toks) and all(t in txt for t in toks)
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--bench", choices=["original", "holdout"], default="original")
args = parser.parse_args()
base = pathlib.Path("benchmark/holdout") if args.bench == "holdout" else pathlib.Path("benchmark")
facts_file = base / ("holdout_facts.csv" if args.bench == "holdout" else "jaldrishti_facts.csv")
registry = json.loads((C / "docs.json").read_text())
discovered = pathlib.Path("cache/discovered.json")
if discovered.exists(): registry += list(json.loads(discovered.read_text()).values())
by_url = {m["url"]: m["file"] for m in registry if m.get("url") and m.get("file")}
out = []
for f in csv.DictReader(open(facts_file, encoding="utf-8")):
    pdf = by_url.get(f["source_url"]) or next((v for k, v in FILES.items() if k in f["source_url"]), None)
    row = {"id": f["fact_id"], "dist": f["district"], "val": f["value"], "page": f["pdf_page_number"]}
    if not pdf: row["status"] = "EXTERNAL"; out.append(row); continue
    p = int(f["pdf_page_number"]); t = norm(page(pdf, p))
    v, q = has_value(t, f["value"]), has_quote(t, f["exact_quote"])
    if v and q: row["status"] = "EXACT"
    elif v: row["status"] = "VALUE_ONLY"
    else:
        hit = [d for d in range(-4, 5) if d and p + d > 0 and has_value(norm(page(pdf, p + d)), f["value"]) and has_quote(norm(page(pdf, p + d)), f["exact_quote"])]
        row["status"] = f"OFFSET{hit[0]:+d}" if hit else "NOT_FOUND"
    # strict: value and a place label (block/village or district) on the same layout line
    if row["status"] == "EXACT":
        labels = [w for w in re.split(r"[\s,/()]+", (f["block_or_village"] or "").lower()) if len(w) > 3] or \
                 [w for w in f["district"].lower().split() if len(w) > 3]
        lines = [norm(l) for l in page(pdf, p).splitlines()]
        row["row_match"] = any(has_value(l, f["value"]) and any(w in l for w in labels) for l in lines)
    out.append(row)
json.dump(out, open(base / "verification.json", "w"), indent=1)
from collections import Counter
print(Counter(r["status"].rstrip("+-0123456789") if r["status"].startswith("OFFSET") else r["status"] for r in out))
for r in out:
    if r["status"] not in ("EXACT", "EXTERNAL") or r.get("row_match") is False: print(r)

if args.bench == "holdout":
    exact = sum(r["status"] == "EXACT" for r in out)
    print(f"Holdout found: {exact}/{len(out)} ({100 * exact / len(out):.1f}%)")
    if not out or exact != len(out): sys.exit(1)
