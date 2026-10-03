"""Ten explicit developer examples against the real CLI. No eval split is loaded."""
import gzip,json,pathlib,subprocess,sys
from jaldrishti.browser_runtime import BrowserRuntime
ROOT=pathlib.Path(__file__).resolve().parents[1]
CASES=[
 ('library','What fluoride is reported at Amtala in Mandirbazar, South 24 Parganas, in April 2022?'),
 ('reference','Can the Karimpur arsenic maximum in Nadia and Bhowmick et al. arsenic mean be treated as the same district mean?'),
 ('library','What is the population-weighted mean fluoride in Nadia?'),
 ('library','What fluoride is listed for Markabera TW WBPR_7 in Purulia?'),
 ('reference','What fluoride is listed for Markabera TW WBPR_7 in Purulia?'),
 ('reference','पुरुलिया में Markabera TW WBPR_7 फ्लोराइड कितना है?'),
 ('reference','পুরুলিয়া জেলা Markabera TW WBPR_7 ফ্লোরাইড কত?'),
 ('reference','What fluoride was measured at Markabera TW WBPR_7 in Purulia on 1 January 2099?'),
 ('reference','What arsenic maximum is reported at Karimpur in Nadia?'),
 ('reference','পুরুলিয়া জেলা অজানাগ্রাম ফ্লোরাইড কত?'),
]

def main():
    runtime=BrowserRuntime(json.loads(gzip.decompress((ROOT/'docs/ask/evidence.json.gz').read_bytes())))
    out=[]
    for n,(scope,q) in enumerate(CASES,1):
        cmd=[str(ROOT/'.venv/bin/jaldrishti'),'ask',q,'--mode',scope,'--offline','--budget','0','--json']
        cli=json.loads(subprocess.check_output(cmd,cwd=ROOT,text=True))
        answer=runtime.ask(q,scope)
        assert cli['credits']==0 and cli['search_attempts']==0
        assert answer==cli['answer'],(n,answer,cli['answer'])
        out.append({'id':f'B{n:02}','scope':scope,'question':q,'answer':answer,'matches_cli':True})
        print(n,answer['answer_type'],flush=True)
    dest=ROOT/'reports/browser_release/parity.json'
    dest.write_text(json.dumps({'label':'post-hoc engineering/dev parity; deliberately selected examples, not accuracy or holdout evidence','command':'jaldrishti ask QUESTION --mode SCOPE --offline --budget 0 --json','credits_used':0,'cases':out},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
