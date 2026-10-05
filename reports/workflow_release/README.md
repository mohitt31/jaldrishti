# October 5 workflow release — post-hoc engineering work

This release completes a narrow research-note workflow over the existing evidence snapshot. It adds no new source harvest, no model tuning and no user-study results. The preceding v0.3.1 corrections are preserved. Frozen original-test and holdout reports remain unchanged and are not rerun.

## Shipped work

- A researcher can save the current question, evidence scope, full answer/refusal, source citations and snapshot hashes into a local note.
- JSON export/import supports an explicit file handoff to a reviewer. Markdown export provides a readable note. No delivery, cloud sync or reviewer authentication is implied.
- Review comments and decisions append separately; they do not modify original measurements or previous comments.
- Imported answers are labelled untrusted/not rechecked. “Recheck with Python” reruns the saved question against the selected current source scope and compares the complete answer plus evidence/engine snapshot identity. A mismatch is shown; imported evidence is not silently replaced. Matching is reproducibility evidence, not independent scientific validation.
- Source cards display exact engine/query/document relations recorded in the existing library manifests. Curated-only sources are labelled. A recorded relation is not proof of first discovery and may involve a previously known local report. The browser does not make live SerpApi requests.
- [The judge-facing evidence page](https://mohitt31.github.io/jaldrishti/review.html) separates functional evidence, historical scores and the still-unmeasured user benefit.
- [The sprint plan](../../planning/OCTOBER_5_8_SPRINT.md), [recruitment drafts](../user_pilot/RECRUITMENT.md) and [draft pilot protocol](../user_pilot/PROTOCOL.md) specify the human work needed before any user-benefit claim.

## Checks and source files

| Check | Evidence | Limitation |
|---|---|---|
| Existing engine and new provenance tests | [checks.json](checks.json): 76 Python tests passing | Synthetic/build-integrity tests; no new accuracy evaluation |
| Note integrity and defensive import | [checks.json](checks.json): 11 Node tests; [test source](../../tests/note.test.mjs) | Review statements remain self-reported; edited JSON is possible and requires recheck |
| Desktop and mobile note export/import/review | [browser_qa.json](browser_qa.json), [checker](../../scripts/check_workflow.cjs) | Headless engineering simulation; synthetic review comments explicitly labelled |
| Imported edit detected; malformed file retained existing note | [browser_qa.json](browser_qa.json) | Tests selected failure cases, not exhaustive security verification |
| CDN failure and retry; network-off after load | [browser_qa.json](browser_qa.json) | Deliberate injected failure; no cold-start offline or physical-phone claim |
| Ten developer examples match Python CLI in each browser layout | [engine_browser_qa.json](engine_browser_qa.json) | Selected development examples; no frozen split is run |
| Initial decoded payload remains below the 3 MB constraint | Exact measured bytes in [engine_browser_qa.json](engine_browser_qa.json) | Before deferred Pyodide; runtime bytes and a universal latency guarantee are excluded |
| Source lineage and snapshot identity | [provenance.json](provenance.json), [public provenance](../../docs/ask/provenance.json), [snapshot](../../docs/ask/snapshot.json) | Historical manifest relation, not live freshness or first-discovery proof |
| Credits and frozen files | [checks.json](checks.json) | Local ledger, not a fresh account-balance query |

The engineering checker's separate browser context simulates transfer of a JSON file; it is **not a second person or a real reviewer**. Exported fixture comments say “Synthetic QA comment” and remain scratch artifacts. They are never included as pilot outcomes.

## Reproduce

```bash
pytest -q
node --test tests/note.test.mjs
python scripts/export_provenance.py  # reads existing manifests only
python -m http.server 8765 --bind 127.0.0.1 --directory docs
# With Playwright and Chrome installed:
node scripts/check_workflow.cjs
QA_OUTPUT=reports/workflow_release/engine_browser_qa.json SCREENSHOT_DIR=work/workflow-screenshots node scripts/check_browser.cjs
```

The site builder also exports provenance after the existing evidence export. No API key is needed. CI runs both browser checkers; CI artifacts are separate from committed historical evaluation files.

## Remaining human work

No participant is confirmed in this task as of the planning check on 5 October. Recruitment drafts have not been sent by the assistant. The pilot task packet and rubric must be verified and locked before timed sessions; the draft protocol is not a completed study. A faculty contact's availability and approval remain unverified. Submission details and final attestations require Mohit's review. Plan target: submit 8 October, 18:00 IST, keeping 9–10 October as contingency rather than a feature-building extension.
