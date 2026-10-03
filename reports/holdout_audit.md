# v0.2 holdout audit (post-run; no rescoring or tuning)

The once-only run at benchmark commit `e2aabb0cbc131c9883846f3e0bd4e8fd7fc149c7` scored **library 17/20; oracle 19/20** under the unchanged evaluation contract. Numeric accuracy was **10/12 and 12/12**. Both modes scored four of five comparisons and all three insufficient-evidence questions correctly by answer type.

The reported scores are not full semantic correctness. Inspection after the run found these limitations:

| Case | Observation |
|---|---|
| HQ11 / HQ12, library | Missing Markabera well evidence: both abstain. Oracle recovers the correct two Purulia well rows. |
| HQ14, both modes | Fails to resolve the comparison between Amdanga habitation and sample counts; returns insufficient evidence instead of not comparable. |
| HQ16, library | Scores correct by answer type but cites Rajasthan/Madhya Pradesh fluoride rows, not Markabera. This is wrong geographical grounding. |
| HQ17, both modes | Scores correct by answer type but selects a different Ramnagar record, 0.29 rather than the specified deeper-aquifer 0.18 row. |
| HQ15, oracle | Scores correct by answer type but selects a different Benajira record, 0.20 rather than the specified April 2022 value 0.29. |
| Nadia evidence metadata | The engine presents `November, 2025` as the period; the gold rows have sampling period UNKNOWN. The report date is not a verified sampling date. |

Consequently, **0% scored risk and 1.00 citation precision must not be presented as zero scientific errors or perfect citations**. The citation metric only re-finds a number on a page. Comparison correctness only checks the answer type. Even numeric scoring does not independently validate every unit/date/place field. No engine changes, question changes, replacement examples or reruns were made after these observations.

## Search accounting

The entire run used `--offline`. The live ledger was **208 before and 208 after**: **zero new live API credits**. The frozen report's library `credits: 1` is the existing search counter counting one unsuccessful offline fallback/cache lookup (HQ14); it is not a billed API request. Oracle reports zero. We retain the raw report and disclose this counter limitation rather than changing the evaluator after the freeze. Harvest cost is 69 recorded credits in total (56 original + 13 supplemental); the supplement also made one unsuccessful HTTP attempt.

The baseline was omitted: the locally recorded usage of 208 against the stated 250-search allowance leaves at most 42, below the requested 60-credit condition. This is ledger-based accounting, not a separately queried account balance.

## Scope and provenance

The holdout has 14 source facts and 20 questions from four existing PDFs. It is place-disjoint from the original fact locations, not source-disjoint, randomized, or independently authored. All 14 facts passed the verifier and were visually checked against PDF row/column headers before the run. See `benchmark/holdout/manifest.json` for physical/printed pages, missing dates, source hashes and scope-specific abstention rationales. An insufficient-evidence label here is not a claim that no evidence exists anywhere.
