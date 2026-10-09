# Baseline: general-purpose AI assistants on the pilot tasks

**This is an automated check of public AI chat assistants, not a user study.** No human participants are involved.

Frozen before any assistant was run (this commit). The six tasks, gold values and rubric are the existing pilot packet (`reports/user_pilot/packet/tasks.json`, `answer_key.json`), unchanged.

## Procedure
- Assistants: ChatGPT, Gemini, DeepSeek (whatever public version is offered on the day; the exact model name shown in the app is recorded with each transcript), each in a fresh chat with web search on, run by the author on 2026-10-09.
- Every assistant gets the identical prompt in `PROMPT.txt` (report title given, no URL, no page hints beyond the M1/M2 page restriction that the task itself defines).
- The full reply is saved unedited in `raw/<assistant>.md` with model name, date and whether search was used.
- NeerTathya answers the same six `engine_question`s from the browser snapshot (library scope) with the CLI, saved in `raw/neertathya.json`.

## Scoring (per task, from `answer_key.json`)
- L1, L2: correct value and unit; correct place and dug well; single-site statistic; April 2022; correct physical page (91). Any invented number or page is scored as a fabrication.
- C1, C2: both values correct; both pages correct; states the wells are different and that two same-month values give no time separation.
- M1, M2: does not assign the April 2022 monthly value to the exact day 15 April; states month-level precision with a citation (header page 90). A refusal with no citation gets partial credit.
- Reported: per-criterion counts, "all criteria met" per task, and fabrications (a number or page that is not on the source page). Failures are kept.

## Known limits
- Three assistants, one run each, one source family (Bankura fluoride rows). Assistant outputs vary between runs and versions.
- Gold rows were checked by an AI assistant, not by an independent human.
- NeerTathya's own known weakness on M1/M2 (generic refusal without citing the monthly row) is scored by the same rubric.

## Round 2 (added 2026-10-09, after round 1 and before any round-2 run)

Round 1 result (kept unchanged): both assistants run so far could not open the report from its title and completed 0/6 tasks, inventing no numbers.

Round 2 removes retrieval and tests reading only: the author uploads the CGWB PDF itself (`corpus/gwq_west_bengal.pdf`, sha256 47f32a59…) to a fresh chat and sends `PROMPT_ROUND2.txt` (the same six tasks; the opening line says the file is attached). Same assistants, same scoring. Saved as `raw/round2_<assistant>.md`. Round 1 and round 2 are reported separately.
