"""Adversarial identity, time, scoring and local API tests; synthetic data only."""
import json,threading,urllib.request,urllib.error
from http.server import HTTPServer
from types import SimpleNamespace
import pytest
from jaldrishti.answer import Engine,score
from jaldrishti.question import parse,Linker,Mention,Query
from jaldrishti.evidence import table_evidence
from jaldrishti.tables import Table
from jaldrishti.strict_evaluate import score_strict
from jaldrishti.server import make_handler


def record(**kw):
    return {'id':'e','doc':'d','page':1,'places':['Testblock','Testvillage'],'location':'Testvillage','district':'Purulia','contaminant':'fluoride',
        'value':0.7,'value_text':'0.7','statistic':'single','unit':'mg/L','source':'TW','well_id':'ABC_1','date':'2023-06-04',
        'period':'2023-06-04','period_basis':'sample_date','spatial_support':'site','row_text':'Testvillage ABC_1 0.7','header':'F mg/L','bbox':None,'threshold':None,**kw}


def engine(records):return Engine(records,{'d':{'title':'Synthetic groundwater report','file':'fake.pdf','url':'https://example.org/fake.pdf','year':2024}})

@pytest.fixture
def verified(monkeypatch):monkeypatch.setattr('jaldrishti.verify.verify_item',lambda *a:True)


def test_unknown_well_does_not_disappear(verified):
    q=parse('What fluoride is reported at Testvillage TW XYZ_99 in Purulia?',Linker([record()]))
    assert q.mentions[0].well_ids==['xyz99']
    assert engine([record()]).ask(q.text)['answer_type']=='insufficient_evidence'

@pytest.mark.parametrize('district',[None,'Bankura'])
def test_wrong_or_unknown_district_cannot_answer(verified,district):
    r=engine([record(district=district)]).ask('What fluoride is reported at Testvillage TW ABC_1 in Purulia?')
    assert r['answer_type']=='insufficient_evidence'


def test_unknown_place_is_not_replaced_by_known_block(verified):
    r=engine([record()]).ask('What fluoride was found at Unknownvillage in Testblock, Purulia?')
    assert r['answer_type']=='insufficient_evidence'


def test_both_operands_need_identity_and_no_partial_answer(verified):
    r=engine([record()]).ask('Can Testvillage TW ABC_1 and Unknownvillage DW XYZ_9 values establish a change?')
    assert r['answer_type']=='insufficient_evidence' and r['items']==[]


def test_shared_block_does_not_make_two_villages_same_point(verified):
    rs=[record(source='TW',well_id=None,date='2023-06-04'),record(id='e2',places=['Testblock','Otherplace'],location='Otherplace',source='TW',well_id=None,date='2023-06-05')]
    r=engine(rs).ask('Can Testvillage and Otherplace values establish a change at the same well?')
    assert r['answer_type']=='not_comparable'
    assert any('same sampling point' in x for x in r['reasons'])


def test_publication_cover_is_never_a_sampling_period():
    t=Table('d',4,0,'lattice',['District','Location','F (mg/L)'],[['Purulia','Testvillage','0.7']])
    ev=table_evidence(t,{'period_text':'November, 2025','year':2025})
    assert ev[0]['period'] is None and ev[0]['publication_year']==2025
    t.caption='Samples collected during Apr, 2022'
    assert table_evidence(t,{'period_text':'November, 2025'})[0]['period']=='Apr, 2022'


def test_unknown_period_cannot_answer_exact_date(verified):
    r=engine([record(date=None,period=None)]).ask('What fluoride was measured at Testvillage in Purulia on 4 June 2023?')
    assert r['answer_type']=='insufficient_evidence'


def test_comparison_page_verification_is_required(monkeypatch):
    monkeypatch.setattr('jaldrishti.verify.verify_item',lambda *a:False)
    rs=[record(),record(id='e2',places=['Otherplace'],location='Otherplace',well_id='ABC_2')]
    r=engine(rs).ask('Can Testvillage and Otherplace values establish a change?')
    assert r['answer_type']=='insufficient_evidence' and not r['items']


def gold_and_item():
    f={'value':'0.7','unit':'mg/L','contaminant':'fluoride','district':'Purulia','block_or_village':'Testvillage','statistic':'single','sampling_period':'04-06-2023','source_url':'https://example.org/fake.pdf','pdf_page_number':'4'}
    i={'value':'0.7','unit':'mg/L','contaminant':'fluoride','district':'Purulia','place':'Testblock, Testvillage','statistic':'single','date':'2023-06-04','url':f['source_url'],'page':4,'page_verified':True}
    return f,i

@pytest.mark.parametrize('field,bad',[('unit','ppb'),('district','Bankura'),('place','Otherplace'),('date','2024-06-04'),('statistic','mean'),('page',5),('contaminant','arsenic')])
def test_strict_scorer_rejects_same_number_wrong_tuple(field,bad):
    f,i=gold_and_item();i[field]=bad
    q={'question_id':'S','supporting_fact_ids':'F','expected_answer_type':'number_with_source'}
    assert not score_strict(q,{'answer_type':'number_with_source','items':[i]},{'F':f})['correct']


def test_strict_scorer_accepts_valid_tuple_and_rejects_unsupported_comparison():
    f,i=gold_and_item();q={'question_id':'S','supporting_fact_ids':'F','expected_answer_type':'number_with_source'}
    assert score_strict(q,{'answer_type':'number_with_source','items':[i]},{'F':f})['correct']
    q['expected_answer_type']='not_comparable'
    assert not score_strict(q,{'answer_type':'not_comparable','items':[],'reasons':['different wells']},{'F':f})['correct']


def test_local_api_validates_requests_and_hides_exception_secrets():
    calls=[]
    class Session:
        api=SimpleNamespace(offline=True,live_credits=0,live_attempts=0,max_live_searches=0)
        def run(self,q,*args,**kwargs):
            calls.append(q)
            if q=='fail':raise RuntimeError('api_key=DO_NOT_EXPOSE')
            return {'answer':{'answer_type':'insufficient_evidence','items':[]}}
    server=HTTPServer(('127.0.0.1',0),make_handler(Session()))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url=f'http://127.0.0.1:{server.server_port}'
    def post(payload,origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        req=urllib.request.Request(url+'/api/ask',json.dumps(payload).encode(),headers)
        try:
            with urllib.request.urlopen(req) as r:return r.status,r.read().decode()
        except urllib.error.HTTPError as e:return e.code,e.read().decode()
    try:
        assert post({'question':'hello'})[0]==200
        assert post({'question':'hello'},'https://external.example')[0]==403
        assert post({'question':42})[0]==400
        code,body=post({'question':'fail'});assert code==503 and 'DO_NOT_EXPOSE' not in body
        assert calls==['hello','fail']
    finally:server.shutdown();server.server_close();thread.join()


def test_count_header_inherits_contaminant_from_caption():
    t=Table('d',1,0,'geometry',['Blocks','habitations affected by (>10 µg/L)'],[['Testblock','17']],caption='Arsenic distributions in Purulia District')
    r=table_evidence(t,{})
    assert r[0]['contaminant']=='arsenic' and r[0]['unit']=='habitations' and r[0]['value']==17


def test_numeric_cell_is_not_a_location():
    t=Table('d',1,0,'lattice',['District','Village','Hot Spot Location','As (ppb)'],[['Nadia','Testvillage','88.53','17.5']])
    r=table_evidence(t,{})
    assert r[0]['location']=='Testvillage'


def test_missing_top_border_row_is_recovered_from_column_geometry():
    from jaldrishti.tables import _leading_row
    columns=[(i*30,60,(i+1)*30,80) for i in range(8)]
    table=SimpleNamespace(rows=[SimpleNamespace(cells=columns,bbox=(0,60,240,80))],bbox=(0,60,240,100))
    words=[{'text':v,'x0':i*30+2,'x1':i*30+24,'top':44,'bottom':52} for i,v in enumerate(['Testplace','TW','7.1','230','24','8','0.42','145'])]
    page=SimpleNamespace(extract_words=lambda **kw:words)
    row,bb=_leading_row(page,table)
    assert row[-2]=='0.42' and row[0]=='Testplace' and bb[1]==43


def test_page_number_occurrence_does_not_substitute_for_the_right_row(monkeypatch,tmp_path):
    import jaldrishti.verify as v
    (tmp_path/'source.pdf').write_bytes(b'placeholder')
    monkeypatch.setattr(v,'CORPUS',tmp_path)
    monkeypatch.setattr(v,'page_text',lambda *a:'Testvillage 0.7 Otherplace 0.4')
    monkeypatch.setattr(v,'row_text',lambda *a:'Otherplace 0.4')
    item={'value':'0.7','page':1,'bbox':[0,0,100,20],'location':'Testvillage'}
    assert not v.verify_item(item,{'file':'source.pdf'})
    monkeypatch.setattr(v,'row_text',lambda *a:'Otherplace 0.7')
    assert not v.verify_item(item,{'file':'source.pdf'})


def test_exceedance_threshold_is_mandatory_and_unit_aware():
    e=record(statistic='count_exceeding',unit='samples',threshold='0.01',header='No. samples As >0.01 mg/L')
    m=Mention(text='How many samples were above 10 µg/L?',places=['testvillage'])
    q=Query(m.text,'fluoride',['Purulia'],'lookup',None,[m])
    assert score(e,m,q,'count_exceeding',{}) is not None
    e['threshold']='0.05'
    assert score(e,m,q,'count_exceeding',{}) is None
