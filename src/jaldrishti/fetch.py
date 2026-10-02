"""Download a source document (PDF, or PubMed abstract via NCBI E-utilities)."""
from __future__ import annotations
import hashlib, json, pathlib, re
from .index import CORPUS

def _session():
    try:
        import truststore; truststore.inject_into_ssl()   # system trust store: fixes incomplete chains (cgwb.gov.in)
    except ImportError:
        pass
    import requests
    s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    return s

def pmid_of(url: str) -> str | None:
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)|[?&]term=(\d+)|/pmid/(\d+)", url or "")
    return next((g for g in (m.groups() if m else []) if g), None)

def fetch(url: str) -> dict | None:
    """Return a docs.json-style record for a newly fetched document, or None."""
    s = _session()
    pm = pmid_of(url)
    if pm:
        r = s.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                  params={"db": "pubmed", "id": pm, "rettype": "abstract", "retmode": "xml"}, timeout=60)
        r.raise_for_status()
        f = CORPUS / f"pubmed_{pm}.xml"; f.write_bytes(r.content)
        return {"id": f"pubmed_{pm}", "file": f.name, "url": f"https://pubmed.ncbi.nlm.nih.gov/{pm}/", "type": "peer_reviewed", "format": "pubmed_xml"}
    r = s.get(url, timeout=120); r.raise_for_status()
    if not r.content.startswith(b"%PDF"): return None
    h = hashlib.sha256(r.content).hexdigest()[:12]
    f = CORPUS / f"web_{h}.pdf"; f.write_bytes(r.content)
    return {"id": f"web_{h}", "file": f.name, "url": url, "type": "web_pdf", "format": "pdf"}

PMID_CACHE = CORPUS.parent / "cache" / "pmid.json"

def pmid_for_title(title: str, offline: bool = False) -> str | None:
    """Resolve a paper title (e.g. from a Scholar result) to a PubMed ID. Answers are cached for offline replay."""
    t = re.sub(r"[^\w\s-]", " ", title or "").strip()
    if len(t) < 20: return None
    cache = json.loads(PMID_CACHE.read_text()) if PMID_CACHE.exists() else {}
    if t in cache: return cache[t]
    if offline: return None
    r = _session().get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                       params={"db": "pubmed", "term": f"{t}[Title]", "retmode": "json", "retmax": 1}, timeout=30)
    if not r.ok: return None
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    cache[t] = ids[0] if ids else None
    PMID_CACHE.write_text(json.dumps(cache, indent=0))
    return cache[t]
