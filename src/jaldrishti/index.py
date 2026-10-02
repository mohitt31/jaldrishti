"""Build and load the evidence index for the local corpus (cached as JSON)."""
from __future__ import annotations
import json, pathlib, hashlib
from .tables import read_tables
from .evidence import table_evidence

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPUS = ROOT / "corpus"
CACHE = ROOT / "cache" / "index"

def docs() -> list[dict]:
    """Corpus registry; metadata learned while indexing (authors, year) is merged in."""
    out = []
    for m in json.loads((CORPUS / "docs.json").read_text()):
        f = CACHE / f"{m['id']}.json"
        if f.exists():
            m = {**json.loads(f.read_text()).get("meta", {}), **{k: v for k, v in m.items() if v is not None}}
        out.append(m)
    return out

def add_doc(meta: dict):
    reg = json.loads((CORPUS / "docs.json").read_text())
    if not any(r["id"] == meta["id"] for r in reg):
        reg.append(meta); (CORPUS / "docs.json").write_text(json.dumps(reg, indent=1))

def sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def build_doc(meta: dict, force=False) -> list[dict]:
    pdf = CORPUS / meta["file"]
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{meta['id']}.json"
    h = sha(pdf)
    if out.exists() and not force:
        d = json.loads(out.read_text())
        if d.get("sha256") == h: return d["evidence"]
    ev = []
    if meta.get("format") == "pubmed_xml":
        from .textfacts import parse_pubmed, text_evidence
        info = parse_pubmed(pdf.read_bytes())
        meta.update({k: info[k] for k in ("title", "authors", "year", "journal")})
        ev = text_evidence(meta, info["title"] + ". " + info["abstract"])
    else:
        for t in read_tables(str(pdf), meta["id"]):
            ev.extend(table_evidence(t, meta))
    for e in ev: e.setdefault("id", f"{meta['id']}:{e['page']}:{e['table']}:{e['row']}:{e['col']}")
    out.write_text(json.dumps({"doc": meta["id"], "sha256": h, "meta": meta, "evidence": ev}))
    return ev

def load(build=True) -> list[dict]:
    ev = []
    for m in docs():
        f = CACHE / f"{m['id']}.json"
        if f.exists(): ev.extend(json.loads(f.read_text())["evidence"])
        elif build: ev.extend(build_doc(m))
    return ev

if __name__ == "__main__":
    import sys, time
    for m in docs():
        if len(sys.argv) > 1 and m["id"] not in sys.argv[1:]: continue
        t = time.time(); ev = build_doc(m, force=True)
        print(m["id"], len(ev), "evidence", f"{time.time()-t:.0f}s", flush=True)
