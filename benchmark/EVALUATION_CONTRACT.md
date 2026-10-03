# JalDrishti evaluation contract (frozen before any system tuning)

Benchmark: `jaldrishti_facts.csv` (60 facts) and `jaldrishti_questions.csv` (30 questions).
- Dev split Q001-Q010: may be used while building.
- Test split Q011-Q030: run once, after the system is frozen. No changes after viewing test output.

Answer types: `number_with_source`, `not_comparable`, `insufficient_evidence`.

Scoring per question:
1. Correct answer type.
2. For `number_with_source`: value and unit match a supporting fact, and the cited document + page contains it.
3. For `not_comparable` / `insufficient_evidence`: the system abstains with a reason and states no number as an answer.
4. Unsupported numbers (not on the cited page) count as errors, even when the answer type is right.

Reported metrics: answer accuracy, citation precision, unsupported-claim rate, abstention precision/recall,
SerpApi credits and wall time per question. Baseline: same question sent to a single fixed Google query
(top PDF only), with an equal credit budget.

Ground-truth check: `scripts/verify_benchmark.py` re-reads each cited PDF page.
53/53 corpus facts found on the cited page (3 checked by hand where table rows wrap).
7 PubMed facts are checked against the abstract text separately.

## Amendment 1 (frozen before the test split is run; dev results only were seen)

Why: dev runs showed that per-question web search rarely reaches the annexure tables these facts live in,
so the system was redesigned as harvest -> library -> answer. These rules replace the baseline line above.

Modes (all use the same reader, parser and page re-read check; only how sources are found differs):
- `baseline`: the question text exactly as typed is sent to Google; up to 3 result pages (3 credits);
  the reader may use only PDFs/abstracts those results link to.
- `library`: a one-off harvest of 56 SerpApi searches over generic district templates
  (`jaldrishti.harvest.queries`, no question text) builds the library; each question may then spend
  at most 1 live search if its source is missing. Harvest credits are reported separately.
- `oracle`: the frozen 9-document corpus, no search. Upper bound for the reader.

Scoring: a numeric item counts as correct if its value equals a supporting fact and either (a) it cites the
gold URL and page, or (b) its cited page prints every token of the gold `exact_quote` (another copy of the
same table). Metric `gold_doc_exact_numeric` reports (a) alone. Also reported: coverage and risk
(selective QA, Kamath et al. 2020), citation precision (cited numbers re-found on the cited page) and
citation recall (gold facts recovered), after ALCE (Gao et al. 2023).

Known limitation: the author of the system had read all 30 question texts while building it (only the
10 dev questions were run). The test split is run once with `--i-understand-test-is-final`.

## Amendment 2 (v0.2; post-hoc fixes, before creation of a fresh holdout)

The v0.1 test results on commit 04b029f remain immutable. Neither the old test evaluator nor its
reports are rerun or edited. The v0.1 error categories motivated these post-hoc changes:

1. Count-answer selection matches the entity requested (samples, blocks, habitations or wells),
   rejects known mismatches, and ranks unknown entities below matches.
2. Abstract extraction links capitalised place tokens from titles and sentences, excluding
   district/geographic stop words and chemical/research vocabulary. Abstract records remain
   study-level evidence. The abstract cache is versioned so old records are refreshed.
3. Library fallback resolves an unnamed district using the existing search-result voting before
   planning. Supported ambiguity is retained as OR. Resolution and retrieval together use at
   most two searches; an offline cache miss still consumes an attempt from that cap.
4. Native PDF documents, pages, text handles and site-rendering bitmaps are explicitly closed,
   including exception paths.
5. Supplemental harvest appends one state-level yearbook PDF query and one aquifer-mapping PDF
   query per existing district (14 generic templates), retains the original library and checkpoints
   progress. No benchmark question text or place names determine these queries.
6. A per-session live HTTP-attempt limit includes retries and allows cached replay after the limit.
7. Package version becomes 0.2.0. Synthetic unit tests cover the changes. The old dev summary is
   preserved as reports/eval_dev_v01.json; new dev results are explicitly post-hoc.
8. Benchmark selection (--bench holdout), source-registry-aware verification (--bench holdout),
   an exclusive holdout-start marker recording commit and input hashes, and a guard against
   overwriting the existing test evaluation are implemented before the freeze.

After this commit, a NEW holdout set will be created from actual pages of documents already in
the library or core corpus. It will exclude every location in the original 60-fact CSV. It contains
20 questions: 12 number_with_source, 5 not_comparable, 3 insufficient_evidence. The source pages
will be visually checked; the page verifier must find every holdout fact. Questions and facts will
be committed and pushed BEFORE running the holdout exactly once, with library and oracle modes.
Baseline is omitted unless at least 60 remaining credits can be established. Evaluation will use
offline cached replay to preserve the remaining student budget; uncached retrieval is unavailable
and must be reported as such. No answer-engine or scoring tuning is allowed after holdout creation.

The existing scoring functions are unchanged. Limitations: numeric matching checks value and
source/page or quote tokens but does not independently check units; citation precision checks the
presence of the number on the page, not the complete measurement tuple; comparison scoring checks
answer type, not semantic validity of its reason. All new holdout facts will therefore retain source
and location provenance for inspection. This is place-disjoint, not source-disjoint or independently
blinded: the same assistant implements and authors the holdout. The original benchmark was already
in its conversation history, although test questions were not reread to design these fixes.

Freeze checks: 27 unit tests pass. Offline dev remains baseline 3/10, library 9/10, oracle 10/10.
The supplement completed 13 new queries (13 ledger credits, 14 HTTP attempts) before its request
cap, giving 27 library documents and 69 total harvest search credits. The four original test report
files have unchanged SHA-256 hashes.
