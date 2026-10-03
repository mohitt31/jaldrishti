"""Pure Python name heuristics shared by retrieval and question parsing."""
import re
NOT_PLACE = set("""What Which How Can Could Does Do Is Are Use Only The April June July May March October Special Drive Annual Ground
Water Quality Report CGWB ADB IMIS NAQUIM Explain Retain Exclude Bengal West North South District Year Book Study Mondal Bhowmick
Table Dug Well Hand Pump India Mark Gaighata-only Annexure Aquifer Management Plan Apr Jan Feb Mar Aug Sep Nov Dec January February August September November December Parganas Characteristics Implications Mitigation Drinking""".split())

def proper_names(text: str) -> list[str]:
    """Candidate place names from capitalisation alone (no corpus lookup, so search does not peek at the answer)."""
    from .gazetteer import find_districts
    toks = re.findall(r"[A-Z][a-zA-Z]+(?:\([A-Za-z]+\))?|[a-z]+|\S", text)
    out, cur = [], []
    for i, tk in enumerate(toks):
        if re.match(r"^[A-Z][a-z]", tk) and tk not in NOT_PLACE and i > 0 and not find_districts(tk):
            cur.append(tk)
        else:
            if cur: out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    return [o for o in out if len(o) > 3 and not re.search(r"et$", o)]
