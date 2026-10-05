"""Publish only recorded manifest relations. No search, network, inference or benchmark input."""
import gzip,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]

def relations(scopes, manifests):
    library=set(scopes['library']); core=set(scopes['reference'])-library
    out={did:{'origin':'library_record' if did in library else 'curated_reference_only','traces':[]} for did in library|core}
    for name,manifest in manifests:
        for position,query in enumerate(manifest.get('queries',[]),1):
            for did in query.get('found',[]):
                if did not in library or did not in out:continue
                out[did]['traces'].append({'manifest':name,'query_number':position,'engine':query['engine'],'query':query['q'],'cached_at_recording':query.get('cached'),'site':query.get('as_sitesearch')})
    return out

def export():
    directory=ROOT/'docs/ask'
    payload=json.loads(gzip.decompress((directory/'evidence.json.gz').read_bytes()))
    names=['cache/library.json','cache/library_v03.json']
    manifests=[(name,json.loads((ROOT/name).read_text())) for name in names]
    data={'label':'Recorded discovery provenance; cached history, not live search or proof of first discovery','documents':relations(payload['scopes'],manifests)}
    (directory/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    hashes={p:hashlib.sha256((directory/p).read_bytes()).hexdigest() for p in ['evidence.json.gz','engine.zip','catalog.json','provenance.json']}
    manifest={'schema':1,'label':'Build snapshot identity; not a sampling or publication date','sha256':hashes,'library_manifests':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in names}}
    (directory/'snapshot.json').write_text(json.dumps(manifest,indent=2)+'\n')
    report={'label':'post-hoc provenance inventory, not a new retrieval evaluation','new_credits':0,'documents':len(data['documents']),'library_documents_with_recorded_trace':sum(v['origin']=='library_record' and bool(v['traces']) for v in data['documents'].values()),'curated_only_documents':sum(v['origin']=='curated_reference_only' for v in data['documents'].values()),'snapshot':manifest,'documents_with_no_recorded_trace':[k for k,v in data['documents'].items() if v['origin']=='library_record' and not v['traces']]}
    (ROOT/'reports/workflow_release/provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Provenance exported without search calls.')
if __name__=='__main__':export()
