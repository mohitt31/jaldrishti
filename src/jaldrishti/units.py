"""Concentration units: detection, normalisation and safe conversion."""
import re
from .gazetteer import norm

# canonical: mg/L ; µg/L == ppb (for dilute water) ; ppm == mg/L
_PATTERNS = [
    (r"µg\s*/?\s*l(\s*\(-1\)|-1|⁻¹)?|ug\s*/\s*l|micro\s*g", "µg/L"),
    (r"\bppb\b", "ppb"),
    (r"\bppm\b", "ppm"),
    (r"mg\s*/\s*l|mg\s*l\s*(-1|⁻¹|\(-1\))|mg\s*l-1|\bmg/l\b", "mg/L"),
]
TO_MG_L = {"mg/L": 1.0, "ppm": 1.0, "µg/L": 1e-3, "ppb": 1e-3}

def detect_unit(text: str) -> str | None:
    t = norm(text)
    for pat, u in _PATTERNS:
        if re.search(pat, t):
            return u
    return None

def to_mg_l(value: float, unit: str) -> float | None:
    f = TO_MG_L.get(unit)
    return None if f is None else value * f
