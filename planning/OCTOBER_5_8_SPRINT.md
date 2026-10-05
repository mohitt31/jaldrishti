# NeerTathya: October 5–8 submission sprint

Planning date: 5 October 2026. Internal submission target: **8 October, 18:00 IST**. Official deadline: **10 October, 23:59 IST**. All dates below are IST. Time allocations, participant counts and gates are targets, not achieved results.

## Outcome and scope

Primary intended user: a geology/environmental researcher preparing a source-backed groundwater evidence note. Problem statement to validate with users: “I need to quote and compare published district/well measurements without losing their location, statistic, sampling period or source context.”

Complete task: **question → cited evidence → comparison/refusal → portable evidence note → reviewer feedback → revised note**. No household safety verdict, district risk ranking, field-visit optimisation, new predictive model, generic chatbot or new framework migration in this sprint.

The most urgent unknown is whether relevant people can complete this task better than with their existing workflow. No pilot participant is currently confirmed. Previous-hackathon competitor descriptions and the cause of losing are user-provided, **UNVERIFIED**; this plan adopts the lessons without asserting those outcomes.

## Daily execution and exit gates

| Date | Build / evidence work | Mohit's human work | Exit gate / fallback |
|---|---|---|---|
| 5 Oct, remaining day | Freeze pilot protocol; implement portable cited note + review import/export; expose source discovery records; prepare recruitment text and judge-page outline. | Personally invite 8–12 relevant contacts as a recruitment target: geology peers, postgraduate/research students, and one faculty/lab reviewer if accessible. Ask what they last used such evidence for. | Note survives export → import → review → re-export with unchanged citations. User sessions tentatively booked; no endorsement assumed. |
| 6 Oct | Finish workflow tests; phone/slow-start/CDN-failure checks; repair task blockers. Freeze the pilot build, task instances and scoring rubric before first timed session. | Target 3–5 relevant participants; run ~30–35 minute sessions. Aim for one domain review, independently of the timed student pilot. | Record every success, failure, assistance and version. At noon, if nobody is booked, switch to available 1–2-user formative feedback rather than wait for five. Do not relabel peers as professionals. |
| 7 Oct | Fix the two most consequential observed issues; retest fixes separately; publish a compact claim → evidence → limitation page; prepare submission text and record a rough demo. | Follow up with available reviewers; check whether evidence-note output is actually useful; narrate or record the screen demo. | 15:00 feature freeze. Human outcomes have actual logs, denominators and limitations; uncollected results explicitly say “not evaluated”. |
| 8 Oct | Full engineering regression, both scopes, desktop/mobile, note round trip, secrets/licences/source checks, Pages/CI checks; final demo under three minutes. | Verify identity/team/AI/existing-project disclosures, review final entry, explicitly submit by 18:00 and retain confirmation. | Public repo and video open in incognito; submitted status confirmed, not merely a draft. |
| 9–10 Oct | Buffer for broken links, critical correctness fixes and organiser clarification. | Check submission remains complete. | No speculative new features or claimed study outcomes. Hard deadline 10 Oct 23:59. |

Plan about 10–12 focused hours a day with meals, breaks and a protected sleep block. Human availability and sound review are constraints AI coding cannot remove. Work packages can continue when Mohit is away, but outreach, consent, authentic feedback and participant attestations cannot be fabricated or silently completed for him.

## Priorities and acceptance tests

1. **User benefit:** complete and review a source-backed note. Export includes original question, scope, selected records, original answer type, failed checks, source URLs/pages, verification level, snapshot hashes, user commentary and clearly self-reported review status. Reviewer comments never overwrite original measurements. No automatic “expert validated” badge.
2. **SerpApi contribution:** show actual saved engine/query → recorded found-document relation → source page. Distinguish a library discovery record from a curated-only source; cached history is not live search or proof of first discovery. Missing provenance is labelled, not inferred. Zero new credits without explicit authorisation.
3. **Pilot:** predeclared ordinary-search/PDF baseline, matched task instances, counterbalanced order, full measurement/citation rubric, failures retained, assistance logged, small-sample limitations. See `reports/user_pilot/PROTOCOL.md`.
4. **Judge comprehension:** first screen says who the tool helps and lets them complete the task. Map supports source coverage. One judge page links claims to exact reports and explains why number-presence checks are weaker than scientific validation.
5. **Reliability:** cold-start loading/timeout/retry, offline-after-load behaviour described honestly, mobile widths, safe rendering of imported notes, immutable evidence fields, payload under 3 MB before Python. No public API-key input.

## Hard boundaries

Do not edit or rerun frozen `eval_test.json`, `runs_test_*`, `eval_holdout.json`, or `runs_holdout_*`; never run the test split. Pilot tasks are separately authored and not imported from frozen benchmark questions. Any reused examples are described as development examples. Preserve old library manifests. Zero new SerpApi calls. No secrets, `.env`, PDFs, XML, `.venv`, or index cache in commits. Preserve the current v0.3.1 fixes and keep all existing tests passing.

The existing evidence engine, browser and map are implemented. Human usefulness, time savings, reviewer approval and real adoption remain **UNVERIFIED until observed**. Five users is a recruitment target, not an evidence claim. Any retest after fixes is a new labelled round, never a replacement of first-session failures.

## Proposed 2:45 screen demo

- 0:00–0:20: a researcher has two numbers and needs a defensible citation/comparison.
- 0:20–0:55: ask; open the original source page and show sampling/publication distinction.
- 0:55–1:25: 332 versus 329 µg/L; the tool refuses to treat a maximum and study mean as the same district mean.
- 1:25–1:50: show the saved SerpApi discovery trail and explicit curated-reference distinction.
- 1:50–2:15: export a note, import it for review, record a correction, export the reviewed note. Label scripted review as a demonstration.
- 2:15–2:35: show actual pilot results if collected; otherwise show engineering checks and plainly say a user-benefit pilot is pending.
- 2:35–2:45: what the product cannot establish; repository and usable browser link.

Record functionality running locally as required. A public Pages link supplements the locally running video. Avoid expensive video production: the rules explicitly exclude production quality from judging.

## Official sources checked 5 October

- [Official event page](https://serpapi.github.io/serpapi-india-hackathon-2026/): deadline and five judging criteria; no fixed weights.
- [Rules](https://serpapi.github.io/serpapi-india-hackathon-2026/rules.html): meaningful SerpApi functionality; accessible repo; locally running screen recording under three minutes; disclosures; explicit submission required.
- [Terms](https://serpapi.github.io/serpapi-india-hackathon-2026/terms.html): drafts do not qualify; third-party materials and personal information responsibilities.

No numeric probability of winning is estimated. Competitor quality and judge preferences cannot be inferred from these materials.
