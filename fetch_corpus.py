import pathlib, hashlib
try:
    import truststore; truststore.inject_into_ssl()
except ImportError:
    print('pip install truststore'); raise
import requests
B = "https://cgwb.gov.in/cgwbpnm/public/uploads/documents/"
urls = {
 "yearbook_2015_16.pdf": B+"1687515522384483915file.pdf",
 "gwq_west_bengal.pdf": B+"170799987922095186file.pdf",
 "annual_gwq_2025.pdf": B+"1762854375262680475file.pdf",
 "naquim_bankura.pdf": B+"16905335181706431115file.pdf",
 "amp_purulia.pdf": B+"1744936456830985840file.pdf",
 "adb_49107-006-sd-01.pdf": "https://www.adb.org/sites/default/files/linked-documents/49107-006-sd-01.pdf",
}
out = pathlib.Path("corpus"); out.mkdir(exist_ok=True)
h = {"User-Agent": "Mozilla/5.0"}
for name, u in urls.items():
    p = out/name
    if p.exists() and p.stat().st_size > 10000:
        print('SKIP', name); continue
    try:
        r = requests.get(u, headers=h, timeout=120); r.raise_for_status()
        p.write_bytes(r.content)
        print("OK ", name, len(r.content)//1024, "KB", hashlib.sha256(r.content).hexdigest()[:12])
    except Exception as e:
        print("FAIL", name, u, e)
