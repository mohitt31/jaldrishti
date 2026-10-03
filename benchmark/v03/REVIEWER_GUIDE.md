# Independent geology review — 10-minute handoff

Purpose: check whether the cited source supports the full measurement and whether a refusal/comparison is scientifically justified. This is a review request template; no professor or other reviewer has yet provided feedback.

1. Launch `jaldrishti serve` locally after restoring/indexing the corpus. The default performs cached/offline searches and cannot spend new API credits.
2. Choose the source scope explicitly: search-discovered library, or library plus curated reference reports. The latter is not evidence of search discovery.
3. Ask one measurement question from your own work, one same-place/different-well or time comparison, and one deliberately unsupported question. Keep notes on which sources you expected before viewing the response.
4. Open each cited PDF at the physical page. Check column header, value, unit, contaminant, place, district, well ID/type, sampling date/period versus publication date, and relevant threshold/count entity. A successful row reread alone does not establish all of these.
5. Record whether the answer is usable, usable with corrections, or misleading; describe the correction in your own words. Do not interpret a regional/historical observation as household safety advice.

Feedback template:

| Question | Expected source/page (before viewing) | Response useful? | Wrong/missing fields | Suggested correction | Manual search time / tool time |
|---|---|---|---|---|---|
| | | | | | |

For an independent v0.3 evaluation, author fresh questions AFTER the implementation freeze and without inspecting outputs. Prefer new source documents and locations. Include concentration values, count entities/thresholds, ambiguous names, sampling-versus-publication dates, distinct wells, and truly unsupported requests. Supply the complete expected tuples and refusal rationale. Commit the reviewed set before one final run. Do not describe the existing v0.2 holdout, now used for development, as independent validation.

Do not include private household addresses, health records or personal phone numbers in feedback intended for the public repository.
