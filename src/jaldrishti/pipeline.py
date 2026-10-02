"""Question -> SerpApi search ladder -> locate/fetch sources -> answer from located sources only."""
from __future__ import annotations
import hashlib, json, re, time
from urllib.parse import urlparse
from .index import docs, load, build_doc, add_doc, CORPUS, sha
from .answer import Engine
from .question import parse, Linker
from .search import SerpApi, results, trusted, plan, baseline, relevant, proper_names, resolve_district_step, district_from_results
from .index import ROOT, CACHE as ICACHE

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
        if not hasattr(self, "extra"): self.extra = {}
        self.reg = docs() + list(self.extra.values()); self.by_id = {d["id"]: d for d in self.reg}
        self.by_url = {nurl(d["url"]): d["id"] for d in self.reg}
        self.by_sha = {}
        for d in self.reg:
            f = CORPUS / d["file"]
            if f.exists() and d.get("format") != "pubmed_xml": self.by_sha[sha(f)] = d["id"]
        self.ev = load() + [e for m in self.extra.values() for e in json.loads((ICACHE / f"{m['id']}.json").read_text())["evidence"]]
    def _discovered(self):
        f = ROOT / "cache/discovered.json"
        return json.loads(f.read_text()) if f.exists() else {}
    def _remember(self, url, meta):
        d = self._discovered(); d[url] = meta
        (ROOT / "cache/discovered.json").write_text(json.dumps(d, indent=1))
    def _use(self, meta):
        """Make a discovered doc visible to this session (index it if needed)."""
        if meta["id"] in self.by_id: return meta["id"]
        build_doc(meta)
        self.extra[meta["id"]] = meta
        self.refresh()
        return meta["id"]
    def _add(self, url, fetched):
        from .fetch import fetch
        known = self._discovered().get(url)
        if known:
            if known.get("same_as"): fetched.append({"url": url, "same_as": known["same_as"]}); return known["same_as"]
            if known.get("rejected"): fetched.append({"url": url, "error": known["rejected"]}); return None
            fetched.append({"url": url, "reused": known["id"]}); return self._use(known)
        try:
            meta = fetch(url)
        except Exception as e:
            fetched.append({"url": url, "error": str(e)[:120]}); return None
        if not meta:
            self._remember(url, {"rejected": "not a PDF"}); fetched.append({"url": url, "error": "not a PDF"}); return None
        f = CORPUS / meta["file"]
        if meta.get("format") != "pubmed_xml":
            dup = self.by_sha.get(sha(f))
            if dup:
                self._remember(url, {"same_as": dup}); fetched.append({"url": url, "same_as": dup}); return dup
            (CORPUS / "discovered").mkdir(exist_ok=True)
            f.rename(CORPUS / "discovered" / f.name); meta["file"] = "discovered/" + f.name
        meta["title"] = meta.get("title") or url
        self._remember(url, meta)
        fetched.append({"url": url, "new_doc": meta["id"]})
        return self._use(meta)
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
                if not u or not trusted(u) or nurl(u) in self.by_url or not relevant(r, self.contaminant, self.scope + proper_names(self._q)): continue
                if tries >= self.k: break
                tries += 1
                d = self._add(u, fetched)
                if d: found.add(d)
        return found
    def run(self, question: str, mode: str = "jaldrishti", budget: int = 3) -> dict:
        t0 = time.time()
        q0 = parse(question, Linker(self.ev)); self.contaminant = q0.contaminant; self._q = question
        if mode == "library":
            return self.run_library(question, t0, budget=1)
        if mode == "oracle":
            core = {d["id"] for d in docs()}
            ans = Engine([e for e in self.ev if e["doc"] in core], self.by_id).ask(question)
            return {"mode": mode, "trace": [], "credits": 0, "located": sorted(core), "answer": ans, "seconds": round(time.time() - t0, 2)}
        located, trace, credits, ans = set(), [], 0, None
        self.scope = list(q0.districts)
        if mode == "baseline":
            steps = [{**baseline(q0), "start": s * 10} for s in range(budget)]
        else:
            names = proper_names(question)
            if names and not q0.districts:      # spend one search to learn the district, then plan with it
                st = resolve_district_step(names[0])
                d = self.api.search(engine="google", q=st["q"]); credits += 0 if d.get("_missing") else 1
                dist = district_from_results(d)
                trace.append({**st, "cached": d.get("_cached", False), "n_results": len(results(d)), "located": [], "fetched": [],
                              "top": [{"rank": r["rank"], "domain": r["domain"], "title": r["title"][:90], "pdf": bool(r["pdf"])} for r in results(d)[:3]],
                              "resolved_district": dist, "answer_type": None})
                if dist:
                    q0.districts = list(dist); self.scope = list(dist)
            steps = plan(q0)[:max(0, budget - credits)]
        for st in steps:
            params = {"engine": st["engine"], "q": st["q"]}
            for k in ("as_ylo", "as_yhi"):
                if st.get(k): params[k] = st[k]
            if st.get("start"): params["start"] = st["start"]
            if st.get("as_sitesearch"): params["as_sitesearch"] = st["as_sitesearch"]
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

    def library_docs(self) -> set:
        from .harvest import LIBRARY
        if not LIBRARY.exists(): return set()
        lib = json.loads(LIBRARY.read_text())
        for did in lib["docs"]:               # make harvested docs visible
            if did not in self.by_id:
                meta = next((m for m in self._discovered().values() if m.get("id") == did), None)
                if meta: self._use(meta)
        return set(lib["docs"])
    def run_library(self, question: str, t0: float, budget: int = 1) -> dict:
        """Answer from the harvested library; spend at most `budget` live searches if a source is missing."""
        libdocs = self.library_docs()
        ans = Engine([e for e in self.ev if e["doc"] in libdocs], self.by_id).ask(question)
        trace, credits, located = [], 0, set(libdocs)
        if not satisfied(ans) and budget:
            q0 = parse(question, Linker(self.ev)); self.contaminant = q0.contaminant; self._q = question
            self.scope = list(q0.districts)
            for st in plan(q0)[:budget]:
                params = {"engine": st["engine"], "q": st["q"]}
                for k in ("as_sitesearch", "as_ylo", "as_yhi"):
                    if st.get(k): params[k] = st[k]
                d = self.api.search(**params); credits += 0 if d.get("_missing") else 1
                res = results(d); fetched = []
                new = self.locate(st, res, fetched); located |= new
                ans = Engine([e for e in self.ev if e["doc"] in located], self.by_id).ask(question)
                trace.append({**st, "cached": d.get("_cached", False), "n_results": len(res), "located": sorted(new), "fetched": fetched,
                              "top": [{"rank": r["rank"], "domain": r["domain"], "title": r["title"][:90], "pdf": bool(r["pdf"])} for r in res[:5]],
                              "answer_type": ans["answer_type"]})
                if satisfied(ans): break
        return {"mode": "library", "trace": trace, "credits": credits, "located": sorted(located & {e["doc"] for e in self.ev}),
                "answer": ans, "seconds": round(time.time() - t0, 2), "library_size": len(libdocs)}
