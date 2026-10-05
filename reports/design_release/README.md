# NeerTathya responsive workspace and public rename

**Label: post-hoc interface engineering, not a new accuracy evaluation or user study.**

The public app is now **NeerTathya** (formerly JalDrishti). The existing repository and Pages addresses, Python module paths, historical reports, browser storage key and JSON schema remain stable so existing links, notes and rechecks continue to work. Both `neertathya` and `jaldrishti` commands invoke the same CLI. This is a product name, not a claim of trademark clearance or worldwide uniqueness.

## What changed

- Desktop question composer with separate example starters; compact mobile layout, multiline input and readable source metadata. Research purpose and household-safety limits are visible before the question.
- Source scope remains explicit. Snapshot-based answering and precomputed row checks are disclosed. Detailed runtime explanation is expandable.
- Answer cards state the submitted question, contaminant, statistic, location, well/source type, sampling period, publication year, physical PDF page and verification strength. Engine outputs and evidence bundle are unchanged.
- Clear loading state and completed-result scrolling. Editing a question clears the stale answer and disables saving it as a new answer. Existing saved notes are retained.
- District-to-question action with keyboard focus; note navigation; larger primary touch targets; skip link; light/dark styles and reduced-motion support.
- Public name in site, local-server title, README, draft pilot material, CLI help and exported note filenames. Imported legacy content and historical source identities are not rewritten.

## Evidence

| Check | File | Limit |
|---|---|---|
| Responsive, keyboard, dark mode, legacy-note compatibility, branded exports, stale-answer clearing | [browser_qa.json](browser_qa.json) | Chromium desktop/mobile emulation; not physical-device or cross-browser testing |
| Ten deliberately selected native-CLI / actual Pyodide answer matches on each desktop and mobile browser | [engine_browser_qa.json](engine_browser_qa.json) | Engineering parity, not unseen scientific accuracy |
| Note export/import/recheck, edited-value detection, unsafe input, loaded-runtime offline use, CDN failure/retry | [workflow_qa.json](workflow_qa.json) | Synthetic reviewers; no real user sessions |
| Unit checks, protected hashes, ledger and file sizes | [checks.json](checks.json) | Hash equality establishes preservation, not scientific correctness |

Reproduce with the site served on port 8765 and Playwright/Chrome available:

```bash
pytest -q
node --test tests/note.test.mjs
node scripts/check_design.cjs
QA_OUTPUT=reports/design_release/engine_browser_qa.json SCREENSHOT_DIR=work/design/engine-screenshots node scripts/check_browser.cjs
WORKFLOW_QA_OUTPUT=reports/design_release/workflow_qa.json WORKFLOW_SCREENSHOTS=work/design/workflow-screenshots node scripts/check_workflow.cjs
```

The live SerpApi ledger stays at 211 recorded credits; this release makes no SerpApi calls. Neither original test nor holdout evaluation was rerun. No measured productivity improvement, user validation, expert endorsement or predicted judging score is claimed.
