# Proposed formative user pilot — no results collected

Status: **DRAFT, NOT YET LOCKED OR RUN**. This document is a proposed protocol; it does not establish benefits. Before the first session, lock the build commit, task packet, allocation schedule, expected answers and rubric in a separate dated manifest. Do not call this an independent validation study.

## Question and participants

Can a geology/environmental research user produce a correctly scoped, cited evidence note more successfully or quickly with JalDrishti than with Google and PDF reading?

Target: 3–5 relevant users; accurately distinguish undergraduate peers, postgraduate researchers and professionals. Convenience recruitment, small sample and developer involvement limit generalisation. A faculty review of one note is separate qualitative feedback, not a timed participant unless that person actually completes the protocol.

## Tasks, baseline and order

Prepare three pairs of different but comparable instances, verified against actual source pages before the session:
1. Find a measurement and report contaminant, value/unit, statistic, place, sampling period or “not stated”, and an exact source/page.
2. Decide whether two specified observations support a stated comparison; cite both and explain the relevant mismatch or support.
3. Handle an explicitly unavailable attribute/time/place in a defined source packet. “Not found in the packet” is not “does not exist anywhere”.

Use new task instances, not frozen test/holdout question files. The existing showcase is a development example, not a study task. Have a person other than the developer check the gold rubric if available; otherwise disclose developer-authored scoring. Do not tune to outcomes after sessions begin.

A = Google + normal PDF viewing; B = JalDrishti. Participants receive the same task type but different instance in the second condition to reduce answer-memory effects. Odd participants receive A then B; even participants B then A. Swap paired instance assignment across participants, record allocation, and disclose any difficulty imbalance. Same device and connection within each participant, no coaching on answers. A is a defined baseline, not a claim to represent every professional's usual workflow.

Each timed task has a **four-minute target cap**, fixed before starting. Six tasks give up to 24 minutes plus introduction and feedback; invite 30–35 minutes. These are scheduling choices, not observed completion times. Adjust once before protocol lock if a dry run shows the cap is unsuitable, and disclose the adjustment. A developer dry run is not a participant.

Record cold-start Python load separately and include it in the first-tool task's end-to-end time. Do not prewarm only the tool condition without disclosing it. Opening the exact PDF is part of each evidence task; broken sources are task failures, not silently excluded observations.

## Scoring and records

Primary outcome: task completed correctly within the cap. Report correct/attempted separately for each condition; preserve failures, timeouts, interruptions and assistance. Check the full tuple and source support, not merely whether the same number appears somewhere on the page.

Secondary outcome: elapsed time. Report raw times/statuses per participant/task. A paired time comparison is restricted to corresponding tasks completed correctly in both conditions, with its exact denominator. Do not drop failures then advertise unconditional percentage time savings. No significance, population-level effectiveness or professional adoption claim from this pilot.

Log participant ID and self-described experience category, task ID, instance, condition/order, build/snapshot ID, timestamps, elapsed seconds, completion status, rubric fields, assistance, observed issue and optional feedback. Keep identities and recordings private; get permission before quoting. Public logs contain no names, emails or source-water addresses.

## Review and retest

Reviewer marks “matches my reading”, “needs correction”, or “not checked”, with a comment tied to a cited record. Such status is self-reported and not an independently authenticated expert credential. Preserve the machine evidence unchanged; any proposed correction is a separate reviewer comment.

Fix the most consequential observed problems after the first round. Retest with new matched instances where possible. Report original and retest rounds separately, including build versions and repeated-participant learning. Never replace failed original rows with successful retests.

## Release gate

Before claiming any user benefit, retain: actual participant count/backgrounds, locked protocol/task manifest, anonymised raw logs, scoring rubric, source/page checks, build IDs, failures and limitations. With no sessions, the correct public status is “not evaluated with users”.
