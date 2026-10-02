"""Question -> SerpApi search ladder -> locate/fetch sources -> answer from located sources only."""
from __future__ import annotations
import hashlib, json, re, time
from urllib.parse import urlparse
from .index import docs, load, build_doc, add_doc, CORPUS, sha
from .answer import Engine
from .question import parse, Linker
from .search import SerpApi, results, trusted, plan

def nurl(u: str) -> str:
    p = urlparse(u or "")
    return (p.netloc.lower().removeprefix("www.") + p.path.rstrip("/")).lower()

MISSING = re.compile(r"^No record|not in the corpus|Could not identify")

def satisfied(ans: dict) -> bool:
    if ans["answer_type"] in ("not_comparable", "comparable"): return True
    if ans["answer_type"] == "number_with_source": return not ans.get("missing")
    return not MISSING.search(ans.get("reason", "")) and not ans.get("needs_source")

class Session:
    def __init__(self, live: bool = False, offline: bool = False, fetch_per_step: int = 2):
        self.api, self.live, self.k = SerpApi(offline=offline), live, fetch_per_step
        self.refresh()
    def refresh(self):
        self.reg = docs(); self.by_id = {d["id"]: d for d in self.reg}
        self.by_url = {nurl(d["url"]): d["id"] for d in self.reg}
        self.by_sha = {}
        for d in self.reg:
            f = CORPUS / d["file"]
            if f.exists() and d.get("format") != "pubmed_xml": self.by_sha[sha(f)] = d["id"]
        self.ev = load()
    def _add(self, url, fetched):
        from .fetch import fetch
        try:
            meta = fetch(url)
        except Exception as e:
            fetched.append({"url": url, "error": str(e)[:120]}); return None
        if not meta: fetched.append({"url": url, "error": "not a PDF"}); return None
        f = CORPUS / meta["file"]
        if meta.get("format") != "pubmed_xml":
            dup = self.by_sha.get(sha(f))
            if dup: fetched.append({"url": url, "same_as": dup}); return dup
        if meta["id"] in self.by_id: return meta["id"]
        meta["title"] = meta.get("title") or url
        add_doc(meta); build_doc(meta); self.refresh()
        fetched.append({"url": url, "new_doc": meta["id"]})
        return meta["id"]
    def locate(self, step: dict, res: list[dict], fetched: list) -> set:
        found, tries = set(), 0
        for r in res:
            for u in (r["pdf"], r["link"]):
                if u and nurl(u) in self.by_url: found.add(self.by_url[nurl(u)])
        if step["engine"] == "google_scholar":
            from .fetch import pmid_for_title
            for r in res[:3]:
                try: pm = pmid_for_title(r["title"]) if self.live or not self.api.offline else None
                except Exception: pm = None
                if not pm: continue
                did = f"pubmed_{pm}"
                if did in self.by_id: found.add(did)
                elif self.live:
                    d = self._add(f"https://pubmed.ncbi.nlm.nih.gov/{pm}/", fetched)
                    if d: found.add(d)
        elif self.live:
            for r in res:
                u = r["pdf"]
                if not u or not trusted(u) or nurl(u) in self.by_url: continue
                if tries >= self.k: break
                tries += 1
                d = self._add(u, fetched)
                if d: found.add(d)
        return found
    def run(self, question: str, mode: str = "jaldrishti", budget: int = 3) -> dict:
        t0 = time.time()
        q0 = parse(question, Linker(self.ev))
        if mode == "oracle":
            ans = Engine(self.ev, self.by_id).ask(question)
            return {"mode": mode, "trace": [], "credits": 0, "located": sorted(self.by_id), "answer": ans, "seconds": round(time.time() - t0, 2)}
        ladder = plan(q0, q0.mentions[0].places if q0.mentions else [])
        steps = ([{**ladder[0], "start": s * 10} for s in range(budget)] if mode == "baseline" else ladder[:budget])
        located, trace, credits, ans = set(), [], 0, None
        for st in steps:
            params = {"engine": st["engine"], "q": st["q"]}
            if st.get("start"): params["start"] = st["start"]
            d = self.api.search(**params)
            credits += 0 if d.get("_missing") else 1
            res = results(d); fetched = []
            new = self.locate(st, res, fetched)
            located |= new
            ev = [e for e in self.ev if e["doc"] in located]
            ans = Engine(ev, self.by_id).ask(question)
            trace.append({**st, "cached": d.get("_cached", False), "missing_cache": d.get("_missing", False), "n_results": len(res),
                          "located": sorted(new), "fetched": fetched,
                          "top": [{"rank": r["rank"], "domain": r["domain"], "title": r["title"][:90], "pdf": bool(r["pdf"])} for r in res[:5]],
                          "answer_type": ans["answer_type"]})
            if satisfied(ans): break
        return {"mode": mode, "trace": trace, "credits": credits, "located": sorted(located), "answer": ans,
                "seconds": round(time.time() - t0, 2)}
