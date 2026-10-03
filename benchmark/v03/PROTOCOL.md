# v0.3: post-hoc development, not a new holdout

The user authorized a new development iteration after reviewing v0.2 failures. Amendment 2's no-tuning condition continues to protect the v0.2 result claim and artifacts. It does not make this new version a fresh evaluation.

Original test questions are not opened or evaluated. All existing reports, the v0.2 holdout CSVs, manifest and run marker stay byte-for-byte unchanged. The v0.2 holdout is now development/regression data; it cannot support an unbiased v0.3 performance claim. Versioned development reports contain both the legacy and stricter scores. No existing report is overwritten.

The strict scorer requires every expected tuple and no extra tuples: value, unit, contaminant, district, place, statistic, sampling period, exact source URL and physical page, plus page verification. Additional well/source/aquifer annotations are transcribed from the previously verified source pages recorded in the holdout manifest. Unknown sampling dates must remain unknown. Comparisons need two supported operands and a reason; semantic correctness of free-form reasoning still needs independent review. Source duplicates with different URLs are conservatively rejected by this scorer. Unit aliases ppb/µg/L and ppm/mg/L are equivalent; cross-scale converted answers are not currently credited.

Development uses synthetic adversarial tests and offline replay. New retrieval, if needed, uses generic district/publisher queries with a cap of 3 live HTTP attempts, within the earlier 25-credit total-work cap (13 already used). The original library manifest is preserved; newly search-discovered sources go into a separate v0.3 overlay with search provenance. Gold URLs are never silently inserted into library mode.

Before making any new generalization claim: freeze v0.3; ask an independent domain reviewer to author/verify new questions and source tuples without consulting system outputs; commit that set; evaluate once. No professor feedback is claimed until actually received. See REVIEWER_GUIDE.md for a review handoff.
