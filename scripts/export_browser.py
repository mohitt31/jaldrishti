"""Export source-derived evidence; never reads benchmark questions or runs evaluation."""
import gzip, hashlib, json, math, pathlib, zipfile
from jaldrishti.answer import _cite
from jaldrishti.index import ROOT, docs
from jaldrishti.pipeline import Session
from jaldrishti.verify import verify_item
from jaldrishti.units import to_mg_l
from jaldrishti.gazetteer import DISTRICTS

MODULES = ('__init__', 'gazetteer', 'units', 'query_helpers', 'question', 'answer', 'locales', 'browser_runtime')

def aggregates(evidence, metas, district_names):
    out = {}
    for district in district_names:
        records = [e for e in evidence if e.get('district') == district]
        group = {'documents': len({e['doc'] for e in records}), 'records': len(records), 'contaminants': {}, 'evidence': []}
        for contaminant in ('arsenic', 'fluoride'):
            rs = [e for e in records if e['contaminant'] == contaminant]
            candidates = []
            for e in rs:
                if not e.get('page_verified') or e.get('non_detect') or e.get('unit') not in ('mg/L','µg/L','ppb','ppm') or e.get('statistic') not in ('single','mean','max','range_max','min','range_min'): continue
                value = to_mg_l(e['value'],e['unit'])
                if value is not None and math.isfinite(value) and value >= 0: candidates.append((value,e))
            maximum = max(candidates,key=lambda x:x[0]) if candidates else None
            group['contaminants'][contaminant] = {'records':len(rs), 'maximum': {'mg_l':maximum[0], 'item':_cite(maximum[1],metas)} if maximum else None}
        for e in records:
            item = _cite(e,metas)
            group['evidence'].append({**item, 'row_verified':e['row_verified'], 'page_verified':e['page_verified']})
        out[district] = group
    return out

def export():
    out=ROOT/'docs/ask';out.mkdir(exist_ok=True)
    session=Session(offline=True); library=session.library_docs(); reference=library | {d['id'] for d in docs()}
    ev=[dict(e) for e in session.ev if e['doc'] in reference]
    # Keep all parser/ranking metadata, but no local paths or unnecessary download metadata.
    metas={k:{key:m.get(key) for key in ('id','title','url','publisher','year','authors','period_text','format') if key in m} for k,m in session.by_id.items() if k in reference}
    for n,e in enumerate(ev):
        try: e['page_verified']=verify_item(_cite(e,session.by_id),session.by_id[e['doc']])
        except Exception as exc: raise RuntimeError(f"Verification failed for {e['id']}: {type(exc).__name__}") from exc
        e['row_verified']=bool(e['page_verified'] and e.get('bbox'))
        if n%500==0: print('Verified',n,'/',len(ev),flush=True)
    payload={'schema':1,'scopes':{'library':sorted(library),'reference':sorted(reference)}, 'metas':metas,'evidence':ev}
    raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()
    (out/'evidence.json.gz').write_bytes(gzip.compress(raw,mtime=0))
    with zipfile.ZipFile(out/'engine.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in MODULES:
            info=zipfile.ZipInfo('jaldrishti/'+name+'.py',(2026,10,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,(ROOT/'src/jaldrishti'/f'{name}.py').read_bytes())
    catalog = {}
    for did, meta in metas.items():
        cached = ROOT/'cache/index'/f'{did}.json'
        im = json.loads(cached.read_text()).get('meta', {}) if cached.exists() else {}
        title = im.get('title') or meta.get('title') or did
        if title.startswith('http'):
            import re
            title = re.sub(r'\s+', ' ', im.get('period_text', '')).strip()[:170] or title
        catalog[did] = {'title':title, 'url':meta.get('url'), 'publisher':meta.get('publisher') or im.get('publisher'), 'year':meta.get('year') or im.get('year')}
    (out/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':')))
    # Map data is smaller if the full evidence list is fetched lazily on selection.
    names=list(DISTRICTS)
    full={scope:aggregates([e for e in ev if e['doc'] in payload['scopes'][scope]],metas,names) for scope in payload['scopes']}
    summary={scope:{d:{k:v for k,v in group.items() if k!='evidence'} for d,group in groups.items()} for scope,groups in full.items()}
    (out/'map.json').write_text(json.dumps(summary,ensure_ascii=False,separators=(',',':')))
    (ROOT/'reports/browser_release/map_inventory.json').write_text(json.dumps({'label':'post-hoc source inventory; not risk or evaluation', 'scopes':summary},ensure_ascii=False,separators=(',',':'))+'\n')
    (out/'districts').mkdir(exist_ok=True)
    for district in names:
        (out/'districts'/f'{district.lower().replace(" ","-")}.json').write_text(json.dumps({s:groups[district]['evidence'] for s,groups in full.items()},ensure_ascii=False,separators=(',',':')))
    report={'label':'post-hoc engineering build; not an accuracy evaluation','evidence_records':len(ev),'documents':len(metas),'verified_rows':sum(e['row_verified'] for e in ev),'verified_page_or_abstract':sum(e['page_verified'] and not e['row_verified'] for e in ev),'unverified':sum(not e['page_verified'] for e in ev),'credits_used':0,'sizes_bytes':{p.name:p.stat().st_size for p in [out/'evidence.json.gz',out/'engine.zip',out/'map.json']},'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'evidence.json.gz',out/'engine.zip']}, 'map_method':'Counts are indexed evidence records, not independent samples. Maxima are the largest finite nonnegative verified concentration value, including summary statistics; counts, percentages and non-detects excluded. No pooling or district-risk inference.'}
    (ROOT/'reports/browser_release/build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__': export()
