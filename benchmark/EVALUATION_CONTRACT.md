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
