"""Explicit post-hoc development replay of the now-retired v0.2 holdout.
Does not load original test questions or write any frozen result paths.
"""
import argparse,csv,hashlib,json,subprocess,time
from pathlib import Path
from jaldrishti.index import ROOT
from jaldrishti.pipeline import Session
from jaldrishti.strict_evaluate import score_strict
from jaldrishti.evaluate import score_one

p=argparse.ArgumentParser();p.add_argument('--out',default='reports/v03_development');args=p.parse_args()
out=(ROOT/args.out).resolve()
if out.parent not in {(ROOT/'reports').resolve(),(ROOT/'work/v03').resolve()}: p.error('Use a versioned reports directory or work/v03 scratch directory')
if out.exists(): p.error('Output directory already exists; do not overwrite a recorded development run')
base=ROOT/'benchmark/holdout'
facts={f['fact_id']:f for f in csv.DictReader((base/'holdout_facts.csv').open())}
qs=list(csv.DictReader((base/'holdout_questions.csv').open()))
annotations=json.loads((ROOT/'benchmark/v03/strict_annotations.json').read_text())
session=Session(offline=True)
summary={'label':'POST-HOC DEVELOPMENT REGRESSION, NOT A NEW HOLDOUT','commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)),'offline':True,'modes':{},'benchmark_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in base.glob('*.csv')}}
out.mkdir(parents=True)
for mode in ('library','oracle'):
 rows=[]
 for q in qs:
  r=session.run(q['question'],mode,budget=2)
  strict=score_strict(q,r['answer'],facts,annotations)
  legacy=score_one(q,r['answer'],facts)
  rows.append(dict(question_id=q['question_id'],question=q['question'],**r,strict_score=strict,legacy_score=legacy))
  print(mode,q['question_id'],strict['correct'],r['answer']['answer_type'],flush=True)
 summary['modes'][mode]={'n':len(rows),'strict_correct':sum(r['strict_score']['correct'] for r in rows),'legacy_correct':sum(r['legacy_score']['correct'] for r in rows),'live_credits':sum(r['credits'] for r in rows),'search_attempts':sum(r['search_attempts'] for r in rows)}
 (out/f'runs_{mode}.json').write_text(json.dumps(rows,indent=2))
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
