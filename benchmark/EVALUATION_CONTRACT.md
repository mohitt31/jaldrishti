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
