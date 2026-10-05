"""Recorded source lineage only; no retrieval or frozen evaluation is run."""
import importlib.util,json,gzip,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('export_provenance',ROOT/'scripts/export_provenance.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_no_inferred_discovery_for_curated_or_missing_trace():
    scopes={'library':['a','b'],'reference':['a','b','c']}
    out=module.relations(scopes,[('manifest',{'queries':[{'engine':'google','q':'water','found':['a','c'],'cached':True}]})])
    assert out['a']['traces'][0]['query']=='water'
    assert out['b']=={'origin':'library_record','traces':[]}
    assert out['c']=={'origin':'curated_reference_only','traces':[]}

def test_shipped_provenance_and_snapshot_are_exact():
    directory=ROOT/'docs/ask'
    data=json.loads(gzip.decompress((directory/'evidence.json.gz').read_bytes()))
    names=['cache/library.json','cache/library_v03.json']
    expected=module.relations(data['scopes'],[(p,json.loads((ROOT/p).read_text())) for p in names])
    assert expected==json.loads((directory/'provenance.json').read_text())['documents']
    snapshot=json.loads((directory/'snapshot.json').read_text())
    for name,digest in snapshot['sha256'].items():assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==digest
    for name,digest in snapshot['library_manifests'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
