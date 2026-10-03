"""Select WB features from the pinned geoBoundaries simplified source. No invented borders."""
import argparse,hashlib,json,pathlib
from jaldrishti.gazetteer import DISTRICTS

ALIASES={'Maldah':'Malda','Darjiling':'Darjeeling','Koch Bihar':'Cooch Behar','Puruliya':'Purulia','Hugli':'Hooghly','Haora':'Howrah','North Twenty Four Parganas':'North 24 Parganas','South Twenty Four Parganas':'South 24 Parganas','Barddhaman':'Purba Bardhaman','Paschim Barddhaman':'Paschim Bardhaman'}

def build(source,metadata,out):
    src=json.loads(source.read_text());features=[]
    for f in src['features']:
        original=f['properties']['shapeName'];name=ALIASES.get(original,original)
        if name not in DISTRICTS:continue
        def rounded(x):
            if isinstance(x,list):return [rounded(y) for y in x]
            return round(x,5)
        features.append({'type':'Feature','properties':{'name':name,'source_name':original,'shapeID':f['properties']['shapeID']},'geometry':{'type':f['geometry']['type'],'coordinates':rounded(f['geometry']['coordinates'])}})
    assert {f['properties']['name'] for f in features}==set(DISTRICTS),set(DISTRICTS)-{f['properties']['name'] for f in features}
    assert len(features)==len(DISTRICTS)
    out.mkdir(exist_ok=True)
    (out/'west-bengal.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')))
    meta=json.loads(metadata.read_text());meta.update(attribution='geoBoundaries / Pathways Data Pvt. Ltd. / lgdirectory.gov.in',license_url='https://opendatacommons.org/licenses/odbl/1-0/',extract_license='ODbL-1.0',transformation='Selected West Bengal district names from upstream simplified GeoJSON; rounded coordinates to 5 decimal places. Source Barddhaman is labelled Purba Bardhaman; Paschim Barddhaman is separate. No new boundary geometry created.',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),aliases=ALIASES,features=len(features))
    (out/'boundary-source.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(len(features),'districts;', (out/'west-bengal.geojson').stat().st_size,'bytes')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=pathlib.Path);p.add_argument('metadata',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('docs/ask'));a=p.parse_args();build(a.source,a.metadata,a.out)
