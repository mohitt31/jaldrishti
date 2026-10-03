"""Re-read the cited page and confirm the number is printed there (independent of the table reader)."""
from __future__ import annotations
import re, functools
from .index import CORPUS

@functools.lru_cache(maxsize=512)
def page_text(file: str, page: int) -> str:
    import pypdfium2 as pdfium
    from .pdftext import page_text as read_page
    with pdfium.PdfDocument(str(CORPUS / file)) as doc:
        return read_page(doc, page - 1)

@functools.lru_cache(maxsize=512)
def row_text(file: str, page: int, bbox: tuple) -> str:
    import pypdfium2 as pdfium
    with pdfium.PdfDocument(str(CORPUS / file)) as doc:
        p = doc[page - 1]
        try:
            text = p.get_textpage()
            try:
                left, top, right, bottom = bbox
                height = p.get_height()
                return text.get_text_bounded(left=left-2, bottom=height-bottom-2, right=right+2, top=height-top+2)
            finally: text.close()
        finally: p.close()

def _n(s): return re.sub(r"(?<=\d),(?=\d{3})", "", s or "")

def verify_item(item: dict, meta: dict) -> bool:
    v = _n(item["value"]).strip()
    if not meta or not (CORPUS / meta.get("file", "")).is_file(): return False
    if meta.get("format") == "pubmed_xml":
        txt = (CORPUS / meta["file"]).read_text(errors="ignore")
    else:
        if not item.get("page"): return False
        txt = page_text(meta["file"], int(item["page"]))
        if item.get("bbox"):
            txt = row_text(meta["file"], int(item["page"]), tuple(item["bbox"]))
            from .gazetteer import compact
            row = compact(txt)
            if item.get("location") and compact(item["location"]) not in row: return False
            if item.get("well_id") and compact(item["well_id"]) not in row: return False
    return re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", _n(txt)) is not None
