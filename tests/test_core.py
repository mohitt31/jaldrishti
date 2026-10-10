"""Unit tests that need no network and no PDFs."""
from jaldrishti.gazetteer import find_districts, compact
from jaldrishti.units import detect_unit, to_mg_l
from jaldrishti.textfacts import text_evidence
from jaldrishti.search import proper_names, district_from_results, relevant
from jaldrishti.question import Linker, parse
from jaldrishti.answer import Engine
from jaldrishti.tables import is_data, is_num
import pytest

@pytest.fixture(autouse=True)
def synthetic_page_verification(monkeypatch):
    # These are reader/selection unit tests; independent verification is tested separately.
    monkeypatch.setattr("jaldrishti.verify.verify_item", lambda item, meta: True)


def ev(**k):
    base = {"doc": "d", "page": 1, "table": 0, "row": 0, "col": 0, "method": "lattice", "header_from": None, "contaminant": "fluoride",
            "statistic": "single", "value_text": "1.0", "value": 1.0, "non_detect": False, "unit": "mg/L", "threshold": None,
            "district": "Purulia", "places": [], "source": None, "well_id": None, "date": None, "period": None, "period_quote": None,
            "spatial_support": "site", "context": "", "header": "F", "row_text": "", "bbox": None, "publication_year": 2024, "id": "x"}
    base.update(k); return base

def test_districts_in_order_and_aliases():
    assert find_districts("NORTH 24 PARAGANAS and Nadia") == ["North 24 Parganas", "Nadia"]
    assert find_districts("Barddhman") == ["Purba Bardhaman"]

def test_units():
    assert detect_unit("Highest Conc. (in mg l-1)") == "mg/L"
    assert detect_unit("As (ppb)") == "ppb"
    assert abs(to_mg_l(141.7, "ppb") - 0.1417) < 1e-12

def test_header_thresholds_are_not_data():
    assert is_num(">10") and not is_data(">10") and is_data("1,366")

def test_compact_matches_well_ids():
    assert compact("RAPU 90") == compact("rapu90") and compact("WBP R_1") == compact("WBPR_1")

def test_abstract_excludes_saliva_urine_and_other_metals():
    t = ("Arsenic in groundwater (range: 12-1064 µg L(-1); mean ± S.D: 329±294 µg L(-1)). Manganese average 202±153 µg L(-1), range of 18-604 µg L(-1). "
         "Urinary F (0.39-20.1 mg/L) excretion. Saliva had mean concentrations of 6.3±7.0 µg As L(-1) (0.70-29 µg L(-1)).")
    got = {(e["statistic"], e["value_text"]) for e in text_evidence({"id": "p", "title": "Nadia"}, t)}
    assert got == {("range_min", "12"), ("range_max", "1064"), ("mean", "329")}

def test_proper_names_do_not_use_corpus():
    assert proper_names("Can the Dhabani M-II value on 20 June 2023 and Damru M-II value establish a change?") == ["Dhabani", "Damru"]

def test_district_vote():
    d = {"knowledge_graph": {"title": "Baduria", "description": "town in North 24 Parganas district"},
         "organic_results": [{"title": "Baduria - Wikipedia", "snippet": "Baduria is a city in North 24 Parganas"}]}
    assert district_from_results(d) == ["North 24 Parganas"]

def test_relevance_filter_rejects_junk():
    assert not relevant({"title": "GDS Online Engagement Schedule", "snippet": "West Bengal Circle", "link": "x.pdf"}, "fluoride")
    assert relevant({"title": "Ground Water Quality of West Bengal", "snippet": "fluoride", "link": "x.pdf"}, "fluoride", ["Nadia"])

def _engine(evs):
    return Engine(evs, {"d": {"id": "d", "file": "none", "url": "u", "title": "t"}})

def test_comparison_refuses_different_wells():
    evs = [ev(places=["Joypur", "Dhabani"], source="M-II", well_id="RAPU85", date="2023-06-20", value_text="1.82", value=1.82, id="a"),
           ev(places=["Joypur", "Damru"], source="M-II", well_id="RAPU96", date="2023-06-21", value_text="2.99", value=2.99, id="b", row=1)]
    r = _engine(evs).ask("Can the Dhabani M-II value on 20 June 2023 and Damru M-II value on 21 June 2023 establish a one-day increase at the same well?")
    assert r["answer_type"] == "not_comparable" and any("same sampling point" in x for x in r["reasons"])

def test_date_question_abstains_when_source_gives_only_period():
    evs = [ev(contaminant="arsenic", statistic="max", places=["Ranjitpara"], period="2015 – 16", value_text="0.405", value=0.405)]
    r = _engine(evs).ask("What exact calendar date was the Ranjitpara arsenic maximum sample collected?")
    assert r["answer_type"] == "insufficient_evidence" and not r["items"]

def test_wrong_period_is_rejected():
    evs = [ev(places=["Bhajanghat"], period="2015-16", value_text="1.11", value=1.11)]
    r = _engine(evs).ask("What fluoride value is reported for the dug well at Bhajanghat in April 2022?")
    assert r["answer_type"] == "insufficient_evidence"

def test_named_study_not_in_corpus_abstains():
    r = _engine([ev()]).ask("What fluoride range does the Mondal et al. paper report?")
    assert r["answer_type"] == "insufficient_evidence" and r.get("needs_source") == ["Mondal"]

def test_comparison_with_district_level_item_without_place():
    evs = [ev(statistic="max", places=[], district=None, spatial_support="district", value_text="2.9", value=2.9, id="a"),
           ev(places=["Belsula"], source="Dug Well", period="Apr, 2022", value_text="0.14", value=0.14, id="b", row=1)]
    r = _engine(evs).ask("Can the NAQUIM study maximum and the April 2022 Belsula dug-well value establish a change in district mean fluoride?")
    assert r["answer_type"] == "not_comparable"

def test_count_columns_are_never_concentrations():
    from jaldrishti.evidence import column_role
    for h in ["Fluoride 1.5 No.", "Habitations 1.0– 1.5 mg/L", "No. samples with arsenic >10 µg/L", "Fluoride >1.5 mg/L No."]:
        r = column_role(h, "Table 12. Fluoride-Affected Blocks in Bankura District")
        assert r and r["statistic"] == "count_exceeding", h
    assert column_role("F (mg/L)", "")["statistic"] == "single"

def test_implausible_concentration_is_dropped():
    from jaldrishti.tables import Table
    from jaldrishti.evidence import table_evidence
    t = Table("d", 1, 0, "lattice", ["Location", "F"], [["Bankura", "1046"], ["Bishnupur", "0.29"]], [], "mg/L fluoride", "")
    vals = [e["value"] for e in table_evidence(t, {})]
    assert 0.29 in vals and 1046 not in vals

def test_exact_day_question_cites_the_month_record_as_context():
    evs = [ev(places=["Shalboni"], source="Dug Well", period="Apr, 2022", value_text="0.32", value=0.32, district="Bankura")]
    r = _engine(evs).ask("What fluoride was measured at Shalboni dug well in Bankura on 15 April 2022?")
    assert r["answer_type"] == "insufficient_evidence" and not r["items"]
    assert r["related"] and r["related"][0]["value"] == "0.32" and "Apr, 2022" in r["reason"]

def _district_records():
    return [ev(places=["Raghunathpur"], location="Raghunathpur", value_text="3.1", value=3.1, id="a", bbox=[0, 0, 1, 1]),
            ev(places=["Jhalda"], location="Jhalda", value_text="1.2", value=1.2, id="b", statistic="max", bbox=[0, 0, 1, 1]),
            ev(places=["Para"], location="Para", value_text="0.4", value=0.4, id="c", bbox=[0, 0, 1, 1])]

def test_question_without_place_explains_and_shows_context_not_an_answer():
    r = _engine(_district_records()).ask("What fluoride is reported in Purulia?")
    assert r["answer_type"] == "insufficient_evidence" and not r["items"]
    assert "None" not in r["reason"] and "names no village" in r["reason"] and "3 fluoride records for Purulia" in r["reason"]
    assert [i["value"] for i in r["related"]] == ["3.1", "1.2", "0.4"] and "Raghunathpur" in r["reason"]

def test_safety_and_trend_questions_are_not_answered_with_a_number():
    e = _engine(_district_records())
    s = e.ask("Is my tube well in Purulia safe to drink?")
    assert s["answer_type"] == "insufficient_evidence" and not s["items"] and "accredited laboratory" in s["reason"]
    t = e.ask("Has fluoride in Purulia increased over time?")
    assert t["answer_type"] == "insufficient_evidence" and "same sampling point" in t["reason"]

def test_question_without_place_shows_only_verified_context():
    e = Engine(_district_records(), {"d": {"title": "T"}}, verifier=lambda i, m: i["value"] != "3.1")
    r = e.ask("What fluoride is reported in Purulia?")
    assert [i["value"] for i in r["related"]] == ["1.2", "0.4"]
