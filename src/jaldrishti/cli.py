"""jaldrishti ask | eval | index | credits"""
from __future__ import annotations
import argparse, json, pathlib, sys, time
from .index import ROOT

def _print_answer(r):
    a = r["answer"]
    print(f"\n[{a['answer_type']}]  credits={r['credits']}  located={', '.join(r['located']) or '-'}")
    for i in a.get("items", []):
        print(f"  {i['value']} {i['unit'] or ''}  {i['statistic']}  @ {i['place']}  ({i.get('date') or i.get('period') or 'period unknown'})")
        print(f"     {i['title']}  p.{i['page']}  {i['url']}")
        print(f"     row: {i['quote'][:140]}")
    for x in a.get("reasons", []): print("  not comparable:", x)
    if a.get("note"): print("  note:", a["note"])
    if a.get("reason"): print("  reason:", a["reason"])
    print("  Not a household safety judgement: test your own source with an accredited lab.")

def main(argv=None):
    ap = argparse.ArgumentParser(prog="jaldrishti")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask"); a.add_argument("question"); a.add_argument("--mode", default="jaldrishti", choices=["library", "jaldrishti", "baseline", "oracle"])
    a.add_argument("--live", action="store_true", help="fetch newly found sources"); a.add_argument("--offline", action="store_true", help="cached search results only")
    a.add_argument("--budget", type=int, default=3); a.add_argument("--json", action="store_true")
    e = sub.add_parser("eval"); e.add_argument("--split", default="dev", choices=["dev", "test"]); e.add_argument("--modes", default="baseline,library,oracle")
    e.add_argument("--live", action="store_true"); e.add_argument("--offline", action="store_true"); e.add_argument("--budget", type=int, default=3)
    e.add_argument("--i-understand-test-is-final", action="store_true")
    sub.add_parser("index"); sub.add_parser("credits")
    hv = sub.add_parser("harvest", help="build the West Bengal evidence library with a fixed SerpApi budget"); hv.add_argument("--budget", type=int, default=40)
    ad = sub.add_parser("add-source", help="fetch a PDF or PubMed URL into the corpus"); ad.add_argument("urls", nargs="+")
    args = ap.parse_args(argv)
    if args.cmd == "index":
        from .index import docs, build_doc
        for m in docs(): print(m["id"], len(build_doc(m, force=True)))
        return
    if args.cmd == "harvest":
        from .pipeline import Session
        from .harvest import harvest
        lib = harvest(Session(live=True), args.budget)
        print(f"library: {len(lib['docs'])} documents for {lib['credits']} credits"); return
    if args.cmd == "add-source":
        from .pipeline import Session
        S = Session(live=True)
        for u in args.urls:
            log = []; d = S._add(u, log); print(u, "->", d, log)
        return
    if args.cmd == "credits":
        f = ROOT / "cache/credits.jsonl"
        rows = [json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []
        print(f"{sum(r['credits'] for r in rows)} credits used in {len(rows)} live searches"); return
    from .pipeline import Session
    if args.cmd == "ask":
        r = Session(live=args.live, offline=args.offline).run(args.question, args.mode, args.budget)
        print(json.dumps(r, indent=1, default=str)) if args.json else _print_answer(r); return
    if args.split == "test" and not args.i_understand_test_is_final:
        sys.exit("The test split is run once, after the freeze. Re-run with --i-understand-test-is-final.")
    from .evaluate import load_bench, score_one, summarise
    facts, qs = load_bench(); qs = [q for q in qs if q["split"] == args.split]
    S = Session(live=args.live, offline=args.offline)
    out = ROOT / "reports"; out.mkdir(exist_ok=True)
    summary = {"split": args.split, "budget": args.budget, "run_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "modes": {}}
    for mode in args.modes.split(","):
        rows, runs = [], []
        for q in qs:
            try:
                r = S.run(q["question"], mode, args.budget)
            except Exception as ex:   # one failed request must not kill the run
                r = {"mode": mode, "trace": [], "credits": 0, "located": [], "seconds": 0,
                     "answer": {"answer_type": "error", "items": [], "reason": f"{type(ex).__name__}: {str(ex)[:160]}"}}
            s = score_one(q, r["answer"], facts) | {"credits": r["credits"], "seconds": r["seconds"]}
            rows.append(s); runs.append({"question_id": q["question_id"], "question": q["question"], **r, "score": s})
            print(f"{mode:10s} {q['question_id']} {'OK' if s['correct'] else 'XX'} {r['answer']['answer_type']:22s} credits={r['credits']}", flush=True)
        sm = summarise(rows) | {"credits": sum(r["credits"] for r in rows), "seconds": round(sum(r["seconds"] for r in rows), 1)}
        summary["modes"][mode] = sm
        (out / f"runs_{args.split}_{mode}.json").write_text(json.dumps(runs, indent=1, default=str))
    (out / f"eval_{args.split}.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))

if __name__ == "__main__":
    main()
