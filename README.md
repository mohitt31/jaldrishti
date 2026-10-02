# JalDrishti

**Cited groundwater arsenic and fluoride evidence for West Bengal, found with SerpApi, checked against the source page, and refused when the evidence does not support the question.**

West Bengal has some of the world's worst groundwater arsenic, and parts of the state have high fluoride. The measurements exist, but they are buried in annexure tables of 100–270 page government reports and in paper abstracts. A search engine finds pages *about* arsenic; it does not hand you "0.16 mg/L at the Bhajanghat dug well, April 2022, page 102". And the most common mistake with these numbers is not a missing value but a bad comparison: a single well's maximum set against a district mean, or two different wells treated as a time series.

JalDrishti answers a question with the exact number, unit, place, period, document and page. Or it says *not comparable* or *insufficient evidence* and explains why.

> Not a household safety tool. A number from a 2022 survey says nothing about your tube well today. Test your own source at an accredited lab.

**Track:** Knowledge & Public Interest

## Results (frozen test split, run once)

20 held-out questions, scored against 60 hand-verified facts. Every mode uses the same reader. Only how sources are found differs.

| Mode | Correct | SerpApi credits | Answers given | Wrong among answered (risk) | Citation precision |
|---|---|---|---|---|---|
| **Baseline**: Google the question as typed (up to 3 pages) | **2 / 20** | 58 | 0 % | – | – |
| **JalDrishti**: harvested library + at most 1 live search | **12 / 20** | 9 (+56 once for the library) | 55 % | **9 %** (1 of 11) | **1.00** |
| Oracle: the 9 gold documents given directly, no search | 17 / 20 | 0 | 80 % | 6 % | 1.00 |

- Dev split (10 questions, used while building): baseline 3/10, JalDrishti 9/10, oracle 10/10.
- *Citation precision*: share of cited numbers that the tool re-finds on the cited page by re-reading the PDF independently of the table reader. Every cited number in every mode passed.
- Full outputs, including every search query, result and fetched file: [`reports/eval_test.json`](reports/eval_test.json) and `reports/runs_test_*.json`.

**What went wrong on test** (analysed after the run; the scores above are not changed):
- Q016, the one wrong committed answer: asked for *samples* above 0.01 mg/L, the reader took the adjacent *blocks* column (23 instead of 64).
- Q019, Q026: the village names in a paper abstract (Khayrasole, Rajnagar) are not linked as places, so the abstract range is not found. Reader fails in oracle mode too.
- Library misses: Q012/Q023 (Bhowmick et al. 2015 was not surfaced by Scholar), Q014 (CGWB Year Book 2015–16 not harvested), Q021/Q022 (Purulia aquifer-mapping keywell tables from 2023 not harvested).

## How it uses SerpApi

1. **Harvest (56 searches, once).** Generic templates over the 13 districts where arsenic or fluoride is reported (`src/jaldrishti/harvest.py`). Several phrasings per district, because Google is erratic on these queries: the same template returns the CGWB report at rank 1 for Nadia and Wikipedia's *Arsenic* page for Malda. Google results give government PDFs; **Google Scholar** results give papers, which are resolved to PubMed abstracts. Library: 23 documents. No benchmark question text is used.
2. **Answer from the library** in about a second. No search needed.
3. **Live fallback (≤ 1 search)** when a question names a source the library lacks. The planner turns question cues into a query: a named study → Scholar with `as_ylo`/`as_yhi`; "Special Drive", "NAQUIM", "ADB" → that publisher via `as_sitesearch`; a village → quoted place name.
4. **Place → district resolution** (`jaldrishti ask --mode jaldrishti`): one search resolves a village to its district from the knowledge graph and snippets. A name found in two districts (Dhabani: Bankura and Purulia) is kept as `(Bankura OR Purulia)` instead of guessing.

Every response is cached by its request parameters (never the key) and logged in a credit ledger, so all runs above can be replayed without an API key.

## How it reads and checks

- **Table reader.** pdfplumber cell grids for ruled tables. For unruled tables, right-aligned numbers are clustered into columns, and header phrases are assigned by x-position. A continuation page inherits the last header, aligned from the right edge (analyte columns sit there). 53/53 gold table facts are recovered from the raw PDFs.
- **Typed evidence.** Every measured cell becomes `{value, unit, statistic, contaminant, place, source type, well id, date or period, spatial support, document, page, row}`. Units are normalised (mg/L, µg/L = ppb).
- **Grounded parsing.** A place in a question counts only if it occurs in an indexed table row. Search queries use capitalised names only, so search never peeks at the corpus.
- **Comparison checker.** "Can A and B establish a change / be averaged / be treated as the same district mean?" is decided by rules: same sampling point (place, source type, well id), same statistic, same spatial support, time separation, same quantity type. The failing checks are listed. Unit conversion is shown, e.g. 0.332 mg/L = 332 µg/L vs 329 µg/L: close numbers, but a single-site maximum versus a study mean.
- **Abstention.** Population-weighted means, exact dates where the source gives only a period, detection limits, and periods the source does not cover are refused with a reason.
- **Page re-read.** Before answering, each number is searched for on the cited page with a second PDF library. Numbers that fail are dropped.

No language model is used at answer time; every output is reproducible.

## Benchmark

`benchmark/` holds 60 facts and 30 questions (10 dev, 20 test; 18 numeric, 8 not comparable, 4 insufficient evidence). Every fact was checked against its source text: 53 against the cited PDF page by `scripts/verify_benchmark.py`, and 7 against PubMed abstracts. The benchmark and the scoring contract ([`benchmark/EVALUATION_CONTRACT.md`](benchmark/EVALUATION_CONTRACT.md)) were committed before the system was built. The protocol change from per-question search to harvest-then-answer (Amendment 1) was committed before the test split was run, after the dev results were seen. Limitation: the author had read all 30 question texts while building.

Metrics follow selective QA (coverage and risk, Kamath et al. 2020) and citation evaluation (ALCE, Gao et al. 2023).

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python3 fetch_corpus.py        # 6 public reports from cgwb.gov.in and adb.org
jaldrishti restore             # every PDF/abstract the recorded runs used
jaldrishti index               # build the evidence index (a few minutes)

# replay the frozen evaluation from the cached SerpApi responses, no key needed
jaldrishti eval --split dev --offline --modes baseline,library,oracle

# ask a question
jaldrishti ask --mode library "What fluoride value is reported for the Daulatabad dug well in April 2022?"

# live search (needs SERPAPI_KEY in .env)
jaldrishti harvest --budget 56
jaldrishti ask --mode jaldrishti --live "How many Baduria samples exceeded 10 µg/L arsenic in the IMIS 2014–2017 table?"
pytest -q
```

## Repository

```
src/jaldrishti/  tables.py (PDF tables) · evidence.py (typed records) · textfacts.py (abstracts)
                 question.py (parsing) · answer.py (lookup, comparison, abstention) · verify.py (page re-read)
                 search.py (SerpApi client, cache, planner) · harvest.py · pipeline.py · evaluate.py · cli.py
benchmark/       facts, questions, evaluation contract
cache/serpapi/   every SerpApi response used (replayable)   cache/credits.jsonl  credit ledger
reports/         dev and test results with full traces
```

Source PDFs are not redistributed. They are downloaded from the publishers' sites.

## AI tools used

As the rules require: Claude (Anthropic) wrote most of the code and ran the experiments under my direction, and ChatGPT helped research the problem and draft the benchmark facts, which were then verified against the source pages. The problem choice, evaluation design and the decisions on what to keep or drop were mine.

## Licence

MIT. Data © the original publishers (CGWB, ADB, the cited journals).
