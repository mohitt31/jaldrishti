# AI-assistant baseline: results

**Automated check of public AI chat assistants, not a user study.** Protocol: [PROTOCOL.md](PROTOCOL.md) (round 1 and round 2 both written down before they were run). Transcripts are unedited in `raw/`. Run by the author on 2026-10-09; exact model versions were not recorded.

| Condition | Assistant | All criteria met (of 6) | Invented numbers/pages |
|---|---|---|---|
| Round 1: report **title only**, web search on | assistant A (app not recorded) | 0 (could not open the report) | 0 |
| Round 1 | assistant B (app not recorded) | 0 (could not open the report) | 0 |
| Round 2: **PDF uploaded** to the chat | DeepSeek | 6 | 0 |
| Round 2 | Gemini | 6 | 0 |
| NeerTathya, library scope (finds the source itself) | — | 4 (+ M1, M2 partial) | 0 |

Scoring against `reports/user_pilot/packet/answer_key.json`: L1 0.04 mg/L p.91; L2 0.73 mg/L p.91; C1 0.79 / 0.34 mg/L p.91, different wells, no time separation; C2 0.19 / 0.33 mg/L p.92, same reasoning; M1/M2 month-level precision only (header p.90), 0.32 and 0.03 mg/L on p.91 not assigned to 15 April. Assistant A stated the different-wells reasoning for C1/C2 without values.

## What this shows
- **Finding the source is the hard part.** Given only the report's title, both assistants tried could not reach the CGWB annexure and completed none of the tasks (to their credit, they invented nothing).
- **Once handed the right PDF, current assistants read these rows correctly**, including the comparison and date-precision traps. On M1/M2 they did better than NeerTathya, which refuses ("no record matches") without citing the April 2022 row; that is a NeerTathya weakness, not a strength.
- NeerTathya's contribution is therefore the part assistants could not do here: discovering the source with SerpApi, and answering deterministically with a page re-read, reproducibly and without a language model at answer time.

## Limits
Two assistants per round, one run each, six tasks from one table of one report; versions not recorded; outputs vary between runs. Round 1 and round 2 used different assistants for at least one slot. The gold rows were checked by an AI assistant, not an independent human.

## Post-hoc fix prompted by this check (v0.3.2)
After this comparison, NeerTathya's exact-day handling was changed: when a day is asked and the source only gives a month, it still answers *insufficient evidence* but now shows the month record as context (M1: "only 'Apr, 2022' … 0.32 mg/L at Shalboni, page 91 … should not be reported as a 2022-04-15 measurement"). The table above shows the result before this fix. Strict development replay is unchanged (17/20, 20/20; `reports/v032_development/`).
