"""Re-read the cited page and confirm the number is printed there (independent of the table reader)."""
from __future__ import annotations
import re, functools
from .index import CORPUS

@functools.lru_cache(maxsize=512)
def page_text(file: str, page: int) -> str:
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(CORPUS / file))
    return doc[page - 1].get_textpage().get_text_range()

def _n(s): return re.sub(r"(?<=\d),(?=\d{3})", "", s or "")

def verify_item(item: dict, meta: dict) -> bool:
    v = _n(item["value"]).strip()
    if not meta or not (CORPUS / meta.get("file", "")).is_file(): return False
    if meta.get("format") == "pubmed_xml":
        txt = (CORPUS / meta["file"]).read_text(errors="ignore")
    else:
        if not item.get("page"): return False
        txt = page_text(meta["file"], int(item["page"]))
    return re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", _n(txt)) is not None
