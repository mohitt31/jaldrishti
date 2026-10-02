"""Read measurement tables from PDF pages.

Two readers: `lattice` (pdfplumber cell grid, for ruled tables) and `geometry`
(clusters right-aligned numbers into columns and assigns header phrases by
x-position, for unruled tables). A table whose first row is already data
inherits the header of a same-width table on the previous page.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict
import pdfplumber

NUM = re.compile(r"^[<>]?\s*\d[\d,]*(\.\d+)?%?$|^\.\d+$")
ND = {"nd", "bdl", "traces", "trace", "n.d.", "bdl.", "-"}

def is_num(s: str) -> bool:
    s = (s or "").strip()
    return bool(NUM.match(s.replace(" ", ""))) if s else False

def is_data(s: str) -> bool:
    """Strict: a printed measurement, not a header threshold like '>10'."""
    s = (s or "").strip()
    return is_num(s) and s[0] not in "<>"

@dataclass
class Table:
    doc: str
    page: int
    idx: int
    method: str
    columns: list[str]
    rows: list[list[str]]
    row_bboxes: list[tuple] = field(default_factory=list)
    caption: str = ""
    note: str = ""
    header_from: int | None = None
    def to_dict(self): return asdict(self)

def tabular_pages(pdf_path: str) -> list[int]:
    """Cheap prefilter: pages with >=4 text lines holding >=3 numbers."""
    import pypdfium2 as pdfium
    keep, doc = [], pdfium.PdfDocument(pdf_path)
    for i in range(len(doc)):
        txt = doc[i].get_textpage().get_text_range()
        n = sum(1 for l in txt.splitlines() if len(re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?![\w])", l)) >= 3)
        if n >= 4: keep.append(i + 1)
    return keep

def _clean(c):
    return re.sub(r"\s+", " ", (c or "").replace("\n", " ")).strip()

def _page_lines(page, top=None, bottom=None):
    words = page.extract_words(x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False)
    lines = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if top is not None and w["bottom"] > top: continue
        if bottom is not None and w["top"] < bottom: continue
        if lines and abs(lines[-1]["top"] - w["top"]) <= 2.5:
            lines[-1]["words"].append(w)
        else:
            lines.append({"top": w["top"], "words": [w]})
    for l in lines:
        l["words"].sort(key=lambda w: w["x0"])
        l["text"] = " ".join(w["text"] for w in l["words"])
    return lines

def _caption_note(page, bbox):
    above = _page_lines(page, top=bbox[1])[-4:]
    below = _page_lines(page, bottom=bbox[3])[:3]
    return " | ".join(l["text"] for l in above), " | ".join(l["text"] for l in below)

def _lattice(page, doc, pno):
    out = []
    for k, t in enumerate(page.find_tables()):
        raw = t.extract()
        if not raw or len(raw) < 2: continue
        ncol = max(len(r) for r in raw)
        raw = [[_clean(c) for c in r] + [""] * (ncol - len(r)) for r in raw]
        bbs = [r.bbox for r in t.rows]
        h = 0
        while h < len(raw) and sum(is_data(c) for c in raw[h]) < 2:
            h += 1
        if h >= len(raw): continue
        hdr = [" ".join(raw[r][j] for r in range(h) if raw[r][j]).strip() for j in range(ncol)]
        keep = [j for j in range(ncol) if any(r[j] for r in raw[h:])]
        cols, last = [], -1
        for j in keep:
            cols.append(" ".join(x for x in hdr[last + 1:j + 1] if x).strip()); last = j
        raw = [[r[j] for j in keep] for r in raw]
        cap, note = _caption_note(page, t.bbox)
        out.append(Table(doc, pno, k, "lattice", cols, raw[h:], bbs[h:], cap, note))
    return out

def _phrases(line, gap=5.0):
    ph, cur = [], [line["words"][0]]
    for w in line["words"][1:]:
        if w["x0"] - cur[-1]["x1"] > gap:
            ph.append(cur); cur = [w]
        else:
            cur.append(w)
    ph.append(cur)
    return [{"text": " ".join(w["text"] for w in p), "x0": p[0]["x0"], "x1": p[-1]["x1"]} for p in ph]

def _geometry(page, doc, pno):
    lines = _page_lines(page)
    def nnum(l): return sum(is_data(w["text"]) for w in l["words"])
    isdata = [nnum(l) >= 2 for l in lines]
    out, i, k = [], 0, 0
    while i < len(lines):
        if not isdata[i]: i += 1; continue
        j = i
        while j + 1 < len(lines) and isdata[j + 1] and lines[j + 1]["top"] - lines[j]["top"] < 30: j += 1
        run = lines[i:j + 1]
        if len(run) >= 4:
            toks = [w for l in run for w in l["words"] if is_data(w["text"])]
            # columns = clusters of right edges
            cl = []
            for w in sorted(toks, key=lambda w: w["x1"]):
                if cl and w["x1"] - cl[-1][-1]["x1"] <= 12: cl[-1].append(w)
                else: cl.append([w])
            cl = [c for c in cl if len(c) >= max(2, len(run) // 3)]
            if len(cl) >= 2:
                spans = [(min(w["x0"] for w in c), max(w["x1"] for w in c)) for c in cl]
                label_edge = spans[0][0] - 2
                rows, bbs = [], []
                for l in run:
                    lab = " ".join(w["text"] for w in l["words"] if w["x1"] <= label_edge)
                    cells = []
                    for (a, b) in spans:
                        hit = [w["text"] for w in l["words"] if is_data(w["text"]) and a - 3 <= w["x1"] <= b + 3]
                        cells.append(hit[0] if hit else "")
                    rows.append([lab] + cells)
                    bbs.append((min(w["x0"] for w in l["words"]), l["top"] - 1,
                                max(w["x1"] for w in l["words"]), max(w["bottom"] for w in l["words"]) + 1))
                # header: up to 6 non-data lines above the run, stop at a 'Table' caption
                head, cap = [], ""
                for l in reversed(lines[max(0, i - 8):i]):
                    if re.match(r"^\s*table\b", l["text"], re.I):
                        cap = l["text"]; break
                    if run[0]["top"] - l["top"] > 90: break
                    head.insert(0, l)
                cols = [[] for _ in range(len(spans) + 1)]
                centers = [(a + b) / 2 for a, b in spans]
                def nearest(xc):
                    return -1 if xc < label_edge else min(range(len(centers)), key=lambda n: abs(centers[n] - xc))
                for l in head:
                    for p in _phrases(l):
                        under = [n for n, c in enumerate(centers) if p["x0"] - 2 <= c <= p["x1"] + 2]
                        if len(under) >= 2:          # spanning group header
                            for n in under: cols[n + 1].append(p["text"])
                        else:
                            for w in [w for w in l["words"] if p["x0"] <= w["x0"] and w["x1"] <= p["x1"]]:
                                cols[nearest((w["x0"] + w["x1"]) / 2) + 1].append(w["text"])
                below = [l["text"] for l in lines[j + 1:j + 4]]
                out.append(Table(doc, pno, k, "geometry", [" ".join(c) for c in cols], rows, bbs,
                                 cap or " | ".join(l["text"] for l in lines[max(0, i - 9):i][:3]), " | ".join(below)))
                k += 1
        i = j + 1
    return out

def read_tables(pdf_path: str, doc: str, pages: list[int] | None = None) -> list[Table]:
    pages = pages or tabular_pages(pdf_path)
    out, prev = [], None
    with pdfplumber.open(pdf_path) as pdf:
        for pno in pages:
            page = pdf.pages[pno - 1]
            ts = _lattice(page, doc, pno)
            if not any(sum(is_num(c) for c in r) >= 2 for t in ts for r in t.rows):
                ts = _geometry(page, doc, pno)
            for t in ts:
                if any(t.columns[1:]):
                    prev = t
                elif prev and pno - prev.page <= 40 and abs(len(prev.columns) - len(t.columns)) <= 2:
                    n, hc = len(t.columns), prev.columns
                    # continuation page: align columns from the right edge (analyte columns sit there)
                    t.columns = hc[-n:] if len(hc) >= n else [""] * (n - len(hc)) + hc
                    t.caption, t.header_from = prev.caption, prev.page
            out.extend(ts)
    return out
