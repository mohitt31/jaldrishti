import json, pathlib, requests
from urllib.parse import urlparse
key = [l.split("=", 1)[1].strip() for l in open(".env") if l.startswith("SERPAPI_KEY")][0]
out = pathlib.Path("pilot"); out.mkdir(exist_ok=True)
qs = [(d, "arsenic") for d in ["Nadia", "North 24 Parganas", "Murshidabad", "Malda"]] + \
     [(d, "fluoride") for d in ["Birbhum", "Bankura", "Purulia"]] + [("Nadia", "fluoride")]
summary = []
for d, c in qs:
    q = f"{c} groundwater {d} West Bengal CGWB report"
    r = requests.get("https://serpapi.com/search.json", params={"engine": "google", "q": q, "gl": "in", "hl": "en", "num": 10, "api_key": key}, timeout=60).json()
    (out / f"google_{d}_{c}.json".replace(" ", "_")).write_text(json.dumps(r, indent=1))
    res = r.get("organic_results", [])
    hosts = [urlparse(x["link"]).netloc for x in res]
    summary.append({"q": q, "n": len(res), "pdf": sum(x["link"].lower().endswith(".pdf") for x in res),
                    "gov": sum(h.endswith(".gov.in") or h.endswith(".nic.in") for h in hosts), "error": r.get("error")})
for d, c in [("Nadia", "arsenic"), ("Birbhum", "fluoride")]:
    r = requests.get("https://serpapi.com/search.json", params={"engine": "google_scholar", "q": f"{c} groundwater {d}", "num": 10, "api_key": key}, timeout=60).json()
    (out / f"scholar_{d}_{c}.json").write_text(json.dumps(r, indent=1))
    summary.append({"q": f"scholar {c} {d}", "n": len(r.get("organic_results", [])), "error": r.get("error")})
(out / "summary.json").write_text(json.dumps(summary, indent=1))
for s in summary:
    print(s["q"], "| results", s["n"], "| pdf", s.get("pdf"), "| gov", s.get("gov"), "| err", s.get("error"))
