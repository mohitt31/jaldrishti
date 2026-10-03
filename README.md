# JalDrishti

**Cited groundwater arsenic and fluoride evidence for West Bengal, found with SerpApi, checked against the source page, and refused when the evidence does not support the question.**

West Bengal has some of the world's worst groundwater arsenic, and parts of the state have high fluoride. The measurements exist, but they are buried in annexure tables of 100–270 page government reports and in paper abstracts. A search engine finds pages *about* arsenic; it does not hand you "0.16 mg/L at the Bhajanghat dug well, April 2022, page 102". And the most common mistake with these numbers is not a missing value but a bad comparison: a single well's maximum set against a district mean, or two different wells treated as a time series.

JalDrishti answers a question with the exact number, unit, place, period, document and page. Or it says *not comparable* or *insufficient evidence* and explains why.

> Not a household safety tool. A number from a 2022 survey says nothing about your tube well today. Test your own source at an accredited lab.

**Track:** Knowledge & Public Interest

[Open the recorded demo](https://mohitt31.github.io/jaldrishti/) — explore all 50 recorded dev, original-test and fresh-holdout answers, including failures. This is a static evidence explorer, not a live query service.

## At a glance

| | Result |
|---|---|
| Frozen test (20 Qs, run once) | **12/20 vs 2/20** for Googling the question, with **9 searches instead of 58** |
| Fresh holdout (new places, written after the v0.2 freeze, run once) | **17/20** (numeric 10/12) |
| Cited numbers re-found on the cited PDF page | **100 %** in every run |
| Bad comparisons (different wells, statistics, periods, spatial support) | refused, with the failing checks listed |
| Reproducible without an API key | every SerpApi response is cached; `jaldrishti eval --offline` |

Known limits, all disclosed below: the holdout audit found two comparisons that scored correct while citing the wrong rows (guarded against in v0.3, post-hoc), and the library does not yet contain the newer Purulia keywell report.

## Results (v0.1 frozen test split, run once)

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

## v0.2 results (post-hoc fixes; fresh-location holdout)

The original test results above remain unchanged. v0.2 fixes were selected after the v0.1 error categories were known; they are **post-hoc**, not an improvement measured on the original test set.

| Development split | Baseline | Library | Oracle |
|---|---:|---:|---:|
| v0.1 | 3/10 | 9/10 | 10/10 |
| v0.2 offline replay after supplemental harvest | 3/10 | 9/10 | 10/10 |

Changes: match the entity in count questions; link capitalised abstract place names; resolve an unnamed district before library fallback (at most two searches including resolution); close native PDF handles; add bounded generic PDF harvest templates. Abstract place extraction is a heuristic and records retain study-level spatial support.

The new holdout was authored after the v0.2 freeze (`e28db33`), committed and pushed before execution (`e2aabb0`), and run **once, offline**, in library and oracle modes. Results are frozen at `502f46a`. The baseline was skipped: 208 recorded live credits against the stated 250-search allowance leaves at most 42, below the 60-credit condition.

| Evaluation set | Baseline | Library | Oracle | New live credits in v0.2 run |
|---|---:|---:|---:|---:|
| v0.1 original test, unchanged | 2/20 | 12/20 | 17/20 | Not rerun |
| v0.2 fresh-location holdout | Not run | **17/20** | **19/20** | **0** |
| v0.2 dev offline replay | 3/10 | 9/10 | 10/10 | 0 |

**Different question sets: 12/20 → 17/20 is not a measured before/after improvement.** Holdout numeric accuracy is library **10/12**, oracle **12/12**. Both score four of five comparisons and three of three insufficient-evidence cases correctly by answer type. Scored coverage is 70% / 80%, scored risk 0% / 0%, and citation precision 1.00 / 1.00.

**The audit found errors that these metrics miss.** Library HQ16 says “not comparable” using Rajasthan/Madhya Pradesh rows instead of Purulia. Both modes select the wrong Ramnagar row in HQ17; oracle selects another Benajira row in HQ15. Nadia records use the report date as a period despite an unknown sampling date. Thus 0% scored risk does **not** mean zero scientific errors, and 1.00 citation precision does **not** mean every citation supports the requested measurement. The unchanged scorer awards comparison credit by answer type. These failures were retained, with no tuning or rerun. See the [post-run audit](reports/holdout_audit.md) and [raw results](reports/eval_holdout.json).

The report's library `credits: 1` counts an unsuccessful offline fallback/cache lookup; **no live API call was made**. The ledger stayed 208 before/after. v0.2 work used **13 additional recorded live credits** (195 → 208) during harvesting, with 14 HTTP attempts including one failure. Historical harvest cost is 69 (56 + 13).

The holdout has 14 facts from four existing PDFs, 20 questions and all eight districts. All 14 values were checked against rendered PDF rows and headers, then passed `python scripts/verify_benchmark.py --bench holdout` (14/14 found). Locations exclude those in the original facts; sources are reused. See [facts](benchmark/holdout/holdout_facts.csv), [questions](benchmark/holdout/holdout_questions.csv) and the [verification manifest](benchmark/holdout/manifest.json). The implementation and benchmark author are the same assistant, so this is not an independently authored blind evaluation. Earlier benchmark content was already in the assistant's conversation history; no test questions were reread for these fixes.

The existing scorer is retained for comparability. Its citation metric checks whether a number occurs on the cited page; it does not independently validate the complete measurement tuple. Numeric matching uses value and document/page (or quote tokens), and does not independently check units. Comparison correctness is scored by answer type, not by a semantic assessment of each reason.

## v0.3 development: stricter evidence and a live local app

v0.3 was explicitly authorized after the v0.2 audit. The original test and v0.2 holdout reports stay frozen. **The former holdout is now development data, not a fresh performance test.** The stricter scoring protocol is in [`benchmark/v03/PROTOCOL.md`](benchmark/v03/PROTOCOL.md).

- Unknown well IDs and requested places remain constraints; a record with the wrong or unknown requested district is rejected. Requested well type, count entity, threshold and sampling date must match.
- Publication-cover text no longer supplies sampling dates. The table/row must establish the sampling period; otherwise it remains unknown.
- Both operands of a comparison must be found and verified. A shared block name does not make two villages the same sampling point. Failed or incomplete comparisons abstain.
- A second PDF reader checks the cited row's number and explicit location/well ID where row bounds exist. Page-only/abstract fallback remains weaker and is labelled. The check is not a complete independent scientific interpretation of every column.
- The reader recovers a missing first continuation row from column geometry and inherits a count column's contaminant from its table caption.
- Strict development scoring checks value, unit, contaminant, district, place, statistic, sampling period, source URL/physical page and verification, with extra well/type/aquifer annotations. It requires both comparison operands; reasoning still needs domain review.

Three additional bounded SerpApi queries cost **3 recorded live credits** (208 → 211; 16 additional credits across v0.2 + v0.3 work). They rediscovered an older source but did **not** locate the newer Purulia keywell report. The [separate search overlay](cache/library_v03.json) preserves provenance and leaves the original library manifest unchanged. No more paid searches were made. A reference mode explicitly adds the already curated corpus; it must not be claimed as SerpApi discovery.

### Interactive query interface

```bash
# after installation, fetch_corpus.py, restore and index (see Run it below)
jaldrishti serve
# open http://127.0.0.1:8766
```

This runs the actual question engine, not recorded responses. It binds to localhost, defaults to offline cached search, keeps the API key server-side, and shows source scope, sampling/publication fields, extracted rows, PDF page links and search accounting. Choose **SerpApi-discovered library** or **Library + curated reference reports** explicitly. `jaldrishti serve --live-searches 3` enables at most three total live HTTP attempts for that server session; it may consume credits. The GitHub Pages site remains the public static results explorer; a Python server is required for live queries.

For a CLI reference lookup: `jaldrishti ask --mode reference --offline "What fluoride is listed for Markabera TW WBPR_7 in Purulia?"`.

The recorded development run on code commit `7d308a2` gives:

| Reused v0.2 questions (post-hoc development) | Strict full-tuple score | Legacy score | New live API credits |
|---|---:|---:|---:|
| Search-discovered library | **17/20** | 17/20 | 0 |
| Oracle: curated core reports supplied | **20/20** | 20/20 | 0 |

Library misses HQ11, HQ12 and HQ16 because the newer Purulia report is not search-discovered; it now abstains instead of substituting unrelated rows. Strict checks now recover the previously wrong count comparison and the specified Ramnagar/Benajira rows, and leave unknown sampling dates unknown. **These are development results after tuning on known failures, not an independent held-out score.** A perfect oracle score on this small reused set does not establish general reliability. The live app's explicit reference mode combines the curated corpus with the discovered library; it is not a separately benchmarked mode.

[Development summary](reports/v03_development/summary.json) and per-question strict field failures are recorded separately under `reports/v03_development/`. The earlier scratch replays were development iterations, not final tests. **52 unit tests pass**. Browser checks exercised actual numeric lookup, missing-source refusal, explicit reference comparison, unknown sampling dates and unsupported dates with zero console errors on desktop/mobile. Do not compare the strict score numerically with the weaker frozen score as though they use the same metric. An independent review and new evaluation are still pending: [reviewer handoff](benchmark/v03/REVIEWER_GUIDE.md). No reviewer endorsement is claimed.

## How it uses SerpApi

1. **Harvest (56 searches, once).** Generic templates over the 13 districts where arsenic or fluoride is reported (`src/jaldrishti/harvest.py`). Several phrasings per district, because Google is erratic on these queries: the same template returns the CGWB report at rank 1 for Nadia and Wikipedia's *Arsenic* page for Malda. Google results give government PDFs; **Google Scholar** results give papers, which are resolved to PubMed abstracts. The v0.1 library contained 23 documents; the post-hoc v0.2 supplement adds 13 completed searches (69 total) and expands it to 27 documents. One additional HTTP attempt failed; the 14-attempt cap stopped the remaining template. No benchmark question text is used.
2. **Answer from the library** in about a second. No search needed.
3. **Live fallback (v0.2: ≤ 2 searches including district resolution)** when a question names a source the library lacks. The planner turns question cues into a query: a named study → Scholar with `as_ylo`/`as_yhi`; "Special Drive", "NAQUIM", "ADB" → that publisher via `as_sitesearch`; a village → quoted place name.
4. **Place → district resolution** (`jaldrishti ask --mode jaldrishti`): one search resolves a village to its district from the knowledge graph and snippets. A name found in two districts (Dhabani: Bankura and Purulia) is kept as `(Bankura OR Purulia)` instead of guessing.

Every successful live response is cached by its request parameters (never the key) and logged in a credit ledger. Recorded outputs can be inspected without an API key, and dev evaluation can be replayed offline. Original-test and holdout commands refuse to overwrite their frozen evaluations.

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
benchmark/       original facts/questions, holdout/, evaluation contract
cache/serpapi/   every SerpApi response used (replayable)   cache/credits.jsonl  credit ledger
reports/         dev, frozen original test, holdout results and post-run audit
```

Source PDFs are not redistributed. They are downloaded from the publishers' sites.

## AI tools used

As the rules require: Claude (Anthropic) wrote most of the code and ran the experiments under my direction, and ChatGPT helped research the problem and draft the benchmark facts, which were then verified against the source pages. OpenAI Codex implemented the post-hoc v0.2 fixes, regression tests, safeguards and holdout tooling; authored the new holdout after the freeze; checked the actual PDF pages; ran the once-only evaluation; audited its failures; and updated the README and recorded-demo site. For v0.3, Codex implemented the stricter matching/scorer, continuation-table fixes, bounded retrieval attempt, local query interface and adversarial tests. The holdout has not received an independent human annotation review. Commits and reports record the sequence. The problem choice, evaluation design and the decisions on what to keep or drop were mine.

## Licence

MIT. Data © the original publishers (CGWB, ADB, the cited journals).
