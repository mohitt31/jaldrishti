"""West Bengal districts, contaminant vocabulary and text normalisation."""
import re

DISTRICTS = {
    "Alipurduar": [], "Bankura": [], "Birbhum": [], "Cooch Behar": ["koch bihar", "coochbehar"],
    "Dakshin Dinajpur": ["south dinajpur"], "Darjeeling": [], "Hooghly": ["hugli", "hooghli"],
    "Howrah": [], "Jalpaiguri": [], "Jhargram": [], "Kalimpong": [], "Kolkata": [],
    "Malda": ["maldah"], "Murshidabad": [], "Nadia": [],
    "North 24 Parganas": ["north 24 paraganas", "n 24 parganas", "uttar 24 parganas"],
    "Paschim Bardhaman": [], "Purba Bardhaman": ["barddhman", "barddhaman", "burdwan", "bardhaman"],
    "Paschim Medinipur": ["west midnapore"], "Purba Medinipur": ["east midnapore"],
    "Purulia": ["puruliya"], "South 24 Parganas": ["south 24 paraganas", "dakshin 24 parganas"],
    "Uttar Dinajpur": ["north dinajpur"],
}
CONTAMINANTS = {
    "arsenic": ["arsenic", "as"],
    "fluoride": ["fluoride", "f", "f-", "f−"],
}

def norm(s: str) -> str:
    s = (s or "").replace("–", "-").replace("—", "-").replace("−", "-")
    s = s.replace("µ", "µ").replace("μ", "µ")
    return re.sub(r"\s+", " ", s).strip().lower()

def compact(s: str) -> str:
    """Spacing/punctuation-insensitive key: 'RAPU 90' == 'rapu90', 'WBPR_1' == 'wbpr 1'."""
    return re.sub(r"[^a-z0-9µ]", "", norm(s))

def _variants():
    out = []
    for d, al in DISTRICTS.items():
        for v in [d.lower()] + al:
            out.append((v, d))
    return sorted(out, key=lambda t: -len(t[0]))
_DV = _variants()

def find_districts(text: str) -> list[str]:
    """Districts named in text, in order of first appearance."""
    t = " " + norm(text) + " "
    found, used = {}, t
    for v, d in _DV:
        pat = r"(?<![a-z0-9])" + re.escape(v).replace(r"\ ", r"\s*") + r"(?![a-z0-9])"
        m = re.search(pat, used)
        if m:
            found.setdefault(d, m.start())
            used = re.sub(pat, lambda x: " " * len(x.group(0)), used)
    return sorted(found, key=found.get)

def find_contaminant(text: str) -> str | None:
    t = norm(text)
    hits = [c for c in CONTAMINANTS if re.search(r"\b" + c + r"\b", t)]
    return hits[0] if len(hits) == 1 else (hits[0] if hits else None)
