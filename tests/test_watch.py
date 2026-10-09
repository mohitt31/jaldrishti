import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("watch", pathlib.Path(__file__).resolve().parents[1] / "scripts/watch_sources.py")
watch = importlib.util.module_from_spec(spec); spec.loader.exec_module(watch)

def test_watch_lists_only_new_trusted_relevant_pdfs():
    d = {"organic_results": [
        {"title": "Ground Water Quality of West Bengal 2024", "link": "https://cgwb.gov.in/new.pdf", "snippet": "fluoride West Bengal"},
        {"title": "Ground Water Quality of West Bengal", "link": "https://cgwb.gov.in/old.pdf", "snippet": "West Bengal"},
        {"title": "GDS schedule West Bengal", "link": "https://indiapost.gov.in/list.pdf", "snippet": "West Bengal circle"},
        {"title": "arsenic West Bengal blog", "link": "https://example.com/a.pdf", "snippet": "groundwater West Bengal"}]}
    got = watch.new_candidates([("q", d)], {watch.nurl("https://cgwb.gov.in/old.pdf")})
    assert [c["url"] for c in got] == ["https://cgwb.gov.in/new.pdf"]

def test_watch_skips_without_key(monkeypatch, capsys):
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    assert watch.main() == 0 and "skipping" in capsys.readouterr().out
