"""Post-hoc regression tests use synthetic records, not held-out questions."""
import time
import pytest
from jaldrishti.answer import score
from jaldrishti.question import Mention, Query, Linker, parse
from jaldrishti.textfacts import text_evidence
from jaldrishti.pdftext import page_text
from jaldrishti.harvest import supplemental_queries
from jaldrishti.pipeline import Session

@pytest.mark.parametrize('entity', ['samples', 'blocks', 'habitations', 'wells'])
def test_count_entity_matches_requested_noun(entity):
    m = Mention(text=f'How many {entity} exceed the threshold?', statistics=['count_exceeding'])
    q = Query(m.text, 'arsenic', [], 'lookup', None, [m])
    def record(unit):
        return {'statistic': 'count_exceeding', 'contaminant': 'arsenic', 'unit': unit, 'places': []}
    assert score(record(entity), m, q, 'count_exceeding', {}) is not None
    for wrong in {'samples', 'blocks', 'habitations', 'wells'} - {entity}:
        assert score(record(wrong), m, q, 'count_exceeding', {}) is None


def test_abstract_places_reach_grounded_linker():
    doc = {'id': 'synthetic', 'title': 'Fluoride in Sundarpur and Chanditala blocks of Bankura district'}
    records = text_evidence(doc, 'Samples were collected from Sundarpur and Chanditala. Fluoride in groundwater ranged from 0.4 to 3.2 mg/L.')
    assert records and all({'Sundarpur', 'Chanditala'} <= set(r['places']) for r in records)
    assert all(not {'Bankura', 'Fluoride', 'Samples', 'West', 'Bengal'} & set(r['places']) for r in records)
    assert set(parse('What fluoride range was found at Sundarpur and Chanditala?', Linker(records)).mentions[0].places) == {'sundarpur', 'chanditala'}


@pytest.mark.parametrize('fails', [False, True])
def test_pdf_text_handles_close_even_on_exception(fails):
    closed = []
    class Text:
        def get_text_range(self):
            if fails: raise RuntimeError('read error')
            return 'text'
        def close(self): closed.append('text')
    class Page:
        def get_textpage(self): return Text()
        def close(self): closed.append('page')
    if fails:
        with pytest.raises(RuntimeError): page_text([Page()], 0)
    else: assert page_text([Page()], 0) == 'text'
    assert closed == ['text', 'page']


def test_library_resolves_ambiguous_district_within_total_budget(monkeypatch):
    import jaldrishti.pipeline as p
    calls, scopes = [], []
    session = Session.__new__(Session)
    class API:
        def search(self, **params):
            calls.append(params)
            return {'organic_results': [{'title': 'Nabagram in Bankura', 'snippet': 'Bankura district'},
                                        {'title': 'Nabagram in Purulia', 'snippet': 'Purulia district'}]}
    session.api = API(); session.ev = []; session.by_id = {}
    session.library_docs = lambda: set()
    session.locate = lambda *args: set()
    def planner(query):
        scopes.append(query.districts)
        return [{'engine': 'google', 'q': '(Bankura OR Purulia) groundwater'}] * 3
    monkeypatch.setattr(p, 'plan', planner)
    result = session.run_library('What fluoride is reported for Nabagram?', time.time(), budget=2)
    assert len(calls) == 2
    assert set(scopes[0]) == {'Bankura', 'Purulia'}
    assert result['trace'][0]['resolve'] == 'Nabagram'


def test_supplement_is_bounded_generic_and_covers_all_districts():
    qs = supplemental_queries()
    assert len(qs) <= 15
    assert len({q['district'] for q in qs if 'district' in q}) == 13
    assert all('filetype:pdf' in q['q'] for q in qs)


def test_live_limit_blocks_http_but_allows_cache(monkeypatch, tmp_path):
    import json
    import jaldrishti.search as s
    monkeypatch.setattr(s, 'CACHE', tmp_path)
    monkeypatch.setenv('SERPAPI_MAX_LIVE_SEARCHES', '0')
    monkeypatch.setattr(s, 'api_key', lambda: 'fake')
    api = s.SerpApi()
    with pytest.raises(RuntimeError, match='limit'): api.search(engine='google', q='uncached')
    params = {'engine': 'google', 'q': 'cached', 'hl': 'en', 'gl': 'in'}
    (tmp_path / f'{api.key_of(params)}.json').write_text(json.dumps({'organic_results': []}))
    assert api.search(engine='google', q='cached')['_cached']


def test_holdout_loader_uses_separate_paths(monkeypatch, tmp_path):
    import jaldrishti.evaluate as e
    base = tmp_path / 'benchmark' / 'holdout'; base.mkdir(parents=True)
    (base / 'holdout_facts.csv').write_text('fact_id,value\nH001,1\n')
    (base / 'holdout_questions.csv').write_text('question_id,split\nHQ01,holdout\n')
    monkeypatch.setattr(e, 'ROOT', tmp_path)
    facts, qs = e.load_bench('holdout')
    assert facts['H001']['value'] == '1' and qs[0]['split'] == 'holdout'


def test_frozen_test_guard_never_calls_evaluator(monkeypatch, tmp_path):
    import jaldrishti.cli as cli
    (tmp_path / 'reports').mkdir()
    (tmp_path / 'reports/eval_test.json').write_text('{}')
    monkeypatch.setattr(cli, 'ROOT', tmp_path)
    with pytest.raises(SystemExit, match='prohibited'):
        cli.main(['eval', '--split', 'test', '--i-understand-test-is-final'])


def test_verify_document_closes_on_failure(monkeypatch, tmp_path):
    import jaldrishti.verify as verify
    import pypdfium2
    events = []
    class Doc:
        def __init__(self, *args): pass
        def __enter__(self): return self
        def __exit__(self, *args): events.append('doc closed')
        def __getitem__(self, i): raise RuntimeError('bad page')
    monkeypatch.setattr(pypdfium2, 'PdfDocument', Doc)
    verify.page_text.cache_clear()
    with pytest.raises(RuntimeError): verify.page_text('synthetic.pdf', 99)
    assert events == ['doc closed']


def test_harvest_preserves_library_when_request_cap_reached(monkeypatch, tmp_path):
    import json
    from types import SimpleNamespace
    import jaldrishti.harvest as h
    from jaldrishti.search import LiveSearchLimit
    lib = tmp_path / 'library.json'
    lib.write_text(json.dumps({'docs': ['old'], 'queries': [], 'credits': 5}))
    monkeypatch.setattr(h, 'LIBRARY', lib)
    class API:
        def search(self, **params): raise LiveSearchLimit('limit')
    result = h.harvest(SimpleNamespace(api=API()), budget=2, supplement=True)
    assert result['docs'] == ['old'] and result['credits'] == 5
    assert 'partial harvest retained' in result['stopped_reason']
