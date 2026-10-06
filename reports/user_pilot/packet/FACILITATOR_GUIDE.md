# Pilot-v1 facilitator guide

Status: packet prepared; **no participants, consent, observations or user benefit recorded**. Engine build is `5a676b9daccad48b937b7197861740fbb70381da`. Use the packet hash manifest to identify the protocol, tasks, source and snapshot. No engine tuning on these tasks was performed.

## Before a session

1. Recruit a relevant adult peer/researcher. Record their actual experience category, not an inferred credential. Explain voluntary participation and obtain consent to anonymous notes/timings. Screen recording and attributed quotes need separate consent. Keep identities/contact details outside Git.
2. Open `facilitator.html` locally (facilitator's device). Default mode is synthetic rehearsal. Choose actual human mode only for an actual consented session. Select the next participant ID and follow `allocation.json` in sequence. Keep the task/rubric desk off the participant's shared screen.
3. Record device, browser, prior familiarity with the project, report, example tasks and answer key. If they have read answers, retain the observation and explicitly classify it as familiar/formative; do not claim unbiased timing evidence.
4. Start the participant in ordinary Google/PDF for A, or the NeerTathya page in library scope for B. Both conditions receive the same report title. No source page preloading, no Python prewarming, and no frozen-answer explorer. A cannot use the app or generative search summaries. Record all deviations. Use the same device/connection.
5. The current live URL can change. Confirm its snapshot against the manifest and record the build actually used. Prefer a local checkout of the pinned build if the live version changes. Do not enter an API key or enable live searches.

## During each task

Show only its card when the timer starts. Do not reveal the gold value, suggested query or page except where the task explicitly defines a source packet. Allow query reformulation. Accept the same plain-text note in both conditions; exporting a native NeerTathya note is optional, outside the primary timed task.

Time from task reveal to “finished”, including Python load, search, source opening and note writing. Mark assistance, interruptions, source failures and timeouts. A four-minute cap is a protocol choice, not an observed result. A task ending after the cap is not a within-cap completion. Do not pause for slow loads or silently discard failures. The timer stops automatically at the cap when the browser can execute; delayed background ticks are retained as elapsed time.

After stopping, paste the participant's actual answer and record observed issues. Score the applicable fields yes/no/pending using the source and answer key. Append the observation and export JSON after each session. This file is private; the repository ignores `pilot/` for local logs. Storage may be disabled; an explicit message then requires immediate export. Do not clear browser storage before exporting.

## Gold rubric

All tasks use CGWB **Ground Water Quality of West Bengal**, Annexure I. Header is **physical PDF page 90 / printed page 83**; rows are **physical 91 / printed 84**, or **physical 92 / printed 85**. Header establishes fluoride column `F`, unit mg/L, shallow/unconfined aquifer, and “Sample collected during Apr, 2022”. [Official report](https://cgwb.gov.in/cgwbpnm/public/uploads/documents/170799987922095186file.pdf#page=90).

| Task | Source-backed expected result | Required interpretation |
|---|---|---|
| L1 | Beliatore, Bankura-II, Dug Well: fluoride **0.04 mg/L**, physical page 91 | Single site measurement, April 2022; not a district mean or safety verdict |
| L2 | Chunpara, Barjora, Dug Well: fluoride **0.73 mg/L**, physical page 91 | Same tuple requirements as L1 |
| C1 | Bikna **0.79 mg/L** and Makurgram **0.34 mg/L**, physical page 91 | Both April 2022, different wells. These rows do not establish a same-well time trend. Spatial comparison is not universally forbidden. |
| C2 | Gholkunda **0.19 mg/L** and Jagadalla **0.33 mg/L**, physical page 92 | Both April 2022, different wells; same reasoning as C1 |
| M1 | Shalboni row, physical 91; sampling header physical 90 | Month is supported; the specified 15 April date is not established by these pages. Do not assign its monthly row's 0.32 mg/L to that exact day. |
| M2 | Bandhakona row, physical 91; header physical 90 | Same date-precision limit; do not assign its monthly row's 0.03 mg/L to that exact day. |

Allow mathematically equivalent unit conversions with correct units; named sampling month April 2022 or Apr, 2022. “Single well measurement” is equivalent to “single”. Exact citation requires original source URL/title plus physical page (or printed page explicitly labelled and correctly mapped). For M tasks both header and row pages are required. A page link alone does not prove the source was opened; observe it. No guessed publication date may substitute for sampling time. No household-safety claim may accompany a passing note.

Primary completion = all required rubric fields yes, completed within cap, without assistance. Keep assisted attempts in attempted denominator and report assistance separately. Leave unscored fields pending; the summarizer marks incomplete scoring rather than claiming validated results.

## Known limits BEFORE sessions

- Narrow Bankura fluoride-table tasks from one familiar source family; not an arsenic or district-coverage benchmark. Source and task familiarity can transfer between conditions despite different instances. Fixed category order adds learning/fatigue effects; allocation alternates condition and instance assignments but does not eliminate them.
- Source rows were visually checked by the same assistant that authored the packet. No independent human gold review is claimed. Selected locations do not occur in the old benchmark fact-location fields; no frozen question split was run.
- Developer readiness checks used these six questions on the existing browser snapshot. All coarse answer types matched; this is selected development evidence, **not six successful human tasks**.
- The two exact-day queries return a generic “No record ... matches” message without citing the monthly evidence. This is weaker than the pilot's full answer standard. A participant must inspect the source header or ask for the supported month. Do not award success for the refusal badge alone. The engine was left unchanged.

## After sessions

Keep original logs unchanged. Remove names and identifying content before any public release; obtain quote consent. Run `python scripts/summarize_pilot.py pilot/PRIVATE-observations.json --output pilot/summary.json`. It rejects synthetic, unconsented, duplicate and retest records; separate those into clearly labelled files without deleting originals. Do not change `kind` to make rehearsal data pass.

Summaries retain failures and show conditional paired times only where both variants were correct and unassisted. Report sample size/backgrounds, mismatched difficulty, prior familiarity and excluded/deviant sessions. No significance, general time-saving percentage or expert endorsement claims. Human review of the anonymised log and scoring remains necessary.

After fixing observed problems, author new instances and use a separate retest packet/round. Never replace initial failures. With zero participants, use `RESULTS_TEMPLATE.md` unchanged: “User pilot not conducted.”
