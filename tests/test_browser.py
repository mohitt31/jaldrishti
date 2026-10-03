"""Browser engineering checks, not a rerun or extension of either frozen evaluation."""
import gzip,json,subprocess,sys,zipfile
from pathlib import Path
import pytest
from jaldrishti.answer import Engine
from jaldrishti.browser_runtime import BrowserRuntime
from jaldrishti.locales import normalize_question
from jaldrishti.gazetteer import find_districts, find_contaminant, DISTRICTS
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('question,district,contaminant',[
 ('नदिया जिला आर्सेनिक अधिकतम कितना है?', 'Nadia','arsenic'),
 ('নদিয়া জেলা আর্সেনিক সর্বোচ্চ কত?', 'Nadia','arsenic'),
 ('পুরুলিয়া জেলা ফ্লোরাইড কত?', 'Purulia','fluoride'),
 ('पुरुलिया में फ्लोराइड कितना है?', 'Purulia','fluoride'),
 ('उत्तर २४ परगना में आर्सेनिक औसत क्या है?', 'North 24 Parganas','arsenic'),
 ('উত্তর ২৪ পরগনা জেলা আর্সেনিক গড় কত?', 'North 24 Parganas','arsenic'),
 ('दक्षिण 24 परगना फ्लोराइड अधिकतम कितना है?', 'South 24 Parganas','fluoride'),
 ('দক্ষিণ ২৪ পরগনা জেলা ফ্লোরাইড সর্বাধিক কত?', 'South 24 Parganas','fluoride'),
 ('মুর্শিদাবাদ জেলা আর্সেনিক কত?', 'Murshidabad','arsenic'),
 ('মালদা জেলা আর্সেনিক কত?', 'Malda','arsenic'),
 ('बीरभूम में फ्लोराइड अधिकतम कितना है?', 'Birbhum','fluoride'),
 ('বাঁকুড়া জেলা ফ্লোরাইড গড় কত?', 'Bankura','fluoride'),
])
def test_language_dictionary(question,district,contaminant):
    text,lang=normalize_question(question)
    assert lang in ('bn','hi')
    assert find_districts(text)==[district]
    assert find_contaminant(text)==contaminant
    assert not any('\u0900'<=c<='\u09ff' for c in text)

def record(**kw):
    return {'id':'e','doc':'d','page':2,'places':['Examplevillage'],'location':'Examplevillage','district':'Purulia','contaminant':'fluoride','value':.7,'value_text':'0.7','statistic':'single','unit':'mg/L','source':'TW','well_id':'ABC_1','date':None,'period':None,'spatial_support':'site','row_text':'Examplevillage ABC_1 0.7','header':'F mg/L','bbox':[1,2,3,4],'threshold':None,'row_verified':True,'page_verified':True,**kw}

def data(rec=None):
    return {'scopes':{'library':[],'reference':['d']},'metas':{'d':{'title':'Synthetic report','url':'https://example.org/source.pdf','year':2025}},'evidence':[rec or record()]}

def test_browser_scope_and_verification():
    r=BrowserRuntime(data());q='What fluoride is reported at Examplevillage in Purulia?'
    assert r.ask(q,'library')['answer_type']=='insufficient_evidence'
    a=r.ask(q,'reference');assert a['answer_type']=='number_with_source' and a['items'][0]['row_verified']
    assert a==Engine(data()['evidence'],data()['metas'],lambda *args:True).ask(q)
    assert BrowserRuntime(data(record(page_verified=False,row_verified=False))).ask(q,'reference')['answer_type']=='insufficient_evidence'
    a=BrowserRuntime(data(record(bbox=None,row_verified=False))).ask(q,'reference')
    assert a['items'][0]['page_verified'] and not a['items'][0]['row_verified']

def test_language_answer_matches_english_and_preserves_unknown_village():
    r=BrowserRuntime(data())
    a=r.ask('पुरुलिया में Examplevillage फ्लोराइड कितना है?','reference')
    b=r.ask('What fluoride is reported at Examplevillage in Purulia?','reference')
    assert a['items']==b['items'] and a['language']=='hi' and a['language_header']
    q='পুরুলিয়া জেলা অজানাগ্রাম ফ্লোরাইড কত?'
    text,lang=normalize_question(q);assert 'অজানাগ্রাম' in text
    a=r.ask(q,'reference');assert a['answer_type']=='insufficient_evidence' and 'অজানাগ্রাম' in a['reason']

@pytest.mark.parametrize('q,scope',[('', 'library'),('x'*2001,'library'),('hi','invalid')])
def test_browser_input_validation(q,scope):
    with pytest.raises(ValueError):BrowserRuntime(data()).ask(q,scope)

def test_bundle_has_no_pdf_or_network_dependency():
    bundle=ROOT/'docs/ask/engine.zip'
    with zipfile.ZipFile(bundle) as z:
        assert not any(x in z.namelist() for x in ['jaldrishti/index.py','jaldrishti/search.py','jaldrishti/verify.py'])
        for name in z.namelist():assert z.read(name)==(ROOT/'src'/name).read_bytes()
    code='import sys;sys.path.insert(0,sys.argv[1]);from jaldrishti.browser_runtime import BrowserRuntime;assert "pdfplumber" not in sys.modules;assert "requests" not in sys.modules'
    subprocess.run([sys.executable,'-I','-S','-c',code,str(bundle)],check=True)

def test_shipped_evidence_and_boundary_integrity():
    d=json.loads(gzip.decompress((ROOT/'docs/ask/evidence.json.gz').read_bytes()))
    assert len({e['id'] for e in d['evidence']})==len(d['evidence'])
    assert set(d['scopes']['library'])<=set(d['scopes']['reference'])
    assert all(e['row_verified']==bool(e['bbox'] and e['page_verified']) for e in d['evidence'])
    assert all('file' not in m for m in d['metas'].values())
    geo=json.loads((ROOT/'docs/ask/west-bengal.geojson').read_text())
    assert {f['properties']['name'] for f in geo['features']}==set(DISTRICTS)
    for f in geo['features']:
        polys=[f['geometry']['coordinates']] if f['geometry']['type']=='Polygon' else f['geometry']['coordinates']
        for p in polys:
            for ring in p:
                assert ring[0]==ring[-1]
                assert all(85<x<90 and 21<y<28 for x,y in ring)

def test_map_counts_and_maxima_are_source_derived():
    import importlib.util
    spec=importlib.util.spec_from_file_location('export_browser',ROOT/'scripts/export_browser.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    rs=[record(value=1000,value_text='1000',unit='µg/L'),record(id='b',value=.5,value_text='.5'),record(id='c',value=999,unit='samples',statistic='count_exceeding'),record(id='d',value=9,page_verified=False),record(id='nd',value=8,non_detect=True)]
    g=m.aggregates(rs,data()['metas'],['Purulia'])['Purulia']
    assert g['documents']==1 and g['contaminants']['fluoride']['records']==5
    assert g['contaminants']['fluoride']['maximum']['mg_l']==1
    assert g['contaminants']['fluoride']['maximum']['item']['evidence_id']=='e'
    assert g['contaminants']['arsenic']['maximum'] is None
