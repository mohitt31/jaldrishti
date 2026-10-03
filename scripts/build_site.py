"""Build docs/ (GitHub Pages): data.json from the recorded runs + crops of every cited table row."""
import json, pathlib, sys
sys.path.insert(0, "src")
import pypdfium2 as pdfium
from PIL import ImageDraw
from jaldrishti.index import docs, CORPUS, ROOT

OUT = ROOT / "docs"; (OUT / "crops").mkdir(parents=True, exist_ok=True)
disc = json.loads((ROOT / "cache/discovered.json").read_text())
META = {d["id"]: d for d in docs()} | {m["id"]: m for m in disc.values() if m.get("id")}
for f in (ROOT / "cache/index").glob("*.json"):
    m = json.loads(f.read_text()).get("meta", {})
    if m.get("id") in META: META[m["id"]] = {**m, **{k: v for k, v in META[m["id"]].items() if v}}

import re
def title_of(did):
    m = META.get(did, {}); t = m.get("title") or ""
    f = ROOT / "cache/index" / f"{did}.json"
    if (not t or t.startswith("http")) and f.exists():
        im = json.loads(f.read_text()).get("meta", {}); t = im.get("title") or t
        if m.get("format") == "pubmed_xml" and im.get("authors"):
            t = f"{im['authors'][0]} et al. {im.get('year') or ''}: {t}"
        m = {**im, **m}
    if t and not t.startswith("http"): return t
    cover = re.sub(r"[^\x20-\x7E]+", " ", m.get("period_text", "") or (json.loads(f.read_text()).get("meta", {}).get("period_text", "") if f.exists() else ""))        # English part of the cover page
    cover = re.sub(r"\s+", " ", cover).strip()
    words = [w for w in cover.split() if len(w) > 1][:16]
    return (" ".join(words) or did)[:110]

def crop(item):
    m = META.get(item["doc"]); bb = item.get("bbox")
    if not m or not bb or not item.get("page") or m.get("format") == "pubmed_xml": return None
    name = f"{item['doc']}_p{item['page']}_{int(bb[1])}.png"
    out = OUT / "crops" / name
    if out.exists(): return name
    s = 2.0
    with pdfium.PdfDocument(str(CORPUS / m["file"])) as pdf:
        page = pdf[int(item["page"]) - 1]
        try:
            bitmap = page.render(scale=s)
            try:
                img = bitmap.to_pil().convert("RGB")
            finally:
                bitmap.close()
        finally:
            page.close()
    W, H = img.size; x0, top, x1, bot = [v * s for v in bb]
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([x0 - 4, top - 3, x1 + 4, bot + 3], outline=(217, 72, 15, 255), width=4, fill=(255, 200, 0, 60))
    img.crop((max(0, x0 - 40), max(0, top - 90), min(W, x1 + 40), min(H, bot + 90))).save(out, optimize=True)
    return name

def slim(r):
    a = r["answer"]
    def it(i):
        return {k: i.get(k) for k in ("value", "unit", "statistic", "place", "district", "source_type", "well_id", "date", "period",
                                      "page", "quote", "header", "page_verified", "url")} | {
            "title": title_of(i["doc"])[:140], "crop": crop(i)}
    return {"answer_type": a["answer_type"], "items": [it(i) for i in a.get("items", [])], "related": [it(i) for i in a.get("related", [])],
            "reasons": a.get("reasons", []), "reason": a.get("reason"), "note": a.get("note"), "credits": r["credits"],
            "correct": r["score"]["correct"],
            "trace": [{"engine": t["engine"], "q": t["q"], "site": t.get("as_sitesearch"), "cached": t.get("cached"),
                       "n": t.get("n_results"), "located": t.get("located"), "district": t.get("resolved_district"),
                       "top": t.get("top", [])[:3]} for t in r.get("trace", [])]}

data = {"summary": {}, "questions": []}
for split in ("dev", "test"):
    data["summary"][split] = json.loads((ROOT / f"reports/eval_{split}.json").read_text())["modes"]
    runs = {m: {r["question_id"]: r for r in json.loads((ROOT / f"reports/runs_{split}_{m}.json").read_text())} for m in ("baseline", "library", "oracle")}
    for qid, r in runs["library"].items():
        data["questions"].append({"id": qid, "split": split, "question": r["question"], "expected": r["score"]["expected"],
                                  "modes": {m: slim(runs[m][qid]) for m in runs}})
lib = json.loads((ROOT / "cache/library.json").read_text())
data["library"] = {"credits": lib["credits"], "docs": [{"id": d, "title": title_of(d), "url": META.get(d, {}).get("url")} for d in lib["docs"]],
                   "queries": [{"engine": q["engine"], "q": q["q"], "found": q["found"]} for q in lib["queries"]]}
(OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False))
print(len(data["questions"]), "questions,", len(list((OUT / "crops").glob("*.png"))), "crops")
