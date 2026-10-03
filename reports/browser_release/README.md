# Browser release — post-hoc engineering checks

This release adds browser interaction to the current evidence snapshot. It does **not** rerun either frozen evaluation, establish new accuracy, or claim independent validation. Original test/holdout files, old library manifests and the credit ledger were hash-checked without modification.

## What is executed

The Pyodide worker imports the shipped `answer.py`, `question.py`, units, gazetteer and name helpers. `BrowserRuntime` selects library or library-plus-core evidence and supplies the precomputed verifier. The native CLI continues to re-read PDF rows at answer time. The build performs the same check on every exported record, retaining `page_verified` and `row_verified`. Page-only/abstract verification never receives a row tick. This check verifies the number and explicit row identity; it is **not** complete independent column/statistic/geography validation.

The static app uses the SerpApi-discovered library snapshot. It cannot run new searches, recover uncached sources, or silently add reference documents. Reference mode explicitly adds the curated corpus. No PDF files, XML files, API keys or local file paths are bundled.

## Engineering results and provenance

- [map_inventory.json](map_inventory.json): post-hoc source-linked counts and maxima for each district and scope, matching the map data exactly.
- [build.json](build.json): source-derived export sizes, hashes, evidence/document counts, row/page verification counts and the map aggregation definition. These are inventory metrics, not accuracy results.
- [parity.json](parity.json): ten selected **development examples**, each compared against the complete JSON answer from `jaldrishti ask QUESTION --mode SCOPE --offline --budget 0 --json`. Includes numeric, comparison, insufficient evidence, both scopes, Hindi/Bengali and an unresolved village. These are deliberately chosen developer examples, not held-out questions.
- [browser_qa.json](browser_qa.json): desktop and mobile headless Chrome executed those same inputs through the real downloaded Pyodide runtime. All ten complete answer objects match the CLI on each device. The report records initial decoded payload bytes, overflow, console/network failures and interaction checks. Initial decoded bytes are a conservative body-size measurement; they are not a universal latency or transfer-speed claim. The Python runtime is deferred until the first question.
- `tests/test_browser.py`: language normalisation, conservative abstention, source scopes, verification strength, dependency isolation, zip/source equality, boundary integrity and source-derived map aggregates. The full suite passes **72 tests** in this round; see [checks.json](checks.json).

The evidence snapshot contains records outside West Bengal or with unresolved districts; only records assigned to the named West Bengal district are counted on its map panel. Counts are indexed records, **not independent samples**, and can repeat or overlap across sources. Maxima are finite, nonnegative verified concentration values (including means and range endpoints), converted to mg/L. Counts, percentages, non-detects and unknown units are excluded from maxima. No exposure estimate or cross-district ranking is computed.

## Boundary provenance

The [official metadata endpoint](https://www.geoboundaries.org/api/current/gbOpen/IND/ADM2/) specifies `boundaryYearRepresented: 2021` and **Open Data Commons Open Database License 1.0** for this particular file. The generic gbOpen CC-BY description must not replace that source-specific licence. See [the exact metadata and transformation](../../docs/ask/boundary-source.json) and [licence notice](../../docs/ask/BOUNDARIES-LICENSE.md).

The district extract selects existing features from the pinned upstream simplified dataset and rounds coordinates to five decimal places. No boundary is inferred from evidence or newly invented. Names are canonicalised through an explicit alias table; for example, the upstream `Barddhaman` feature is labelled Purba Bardhaman while the distinct `Paschim Barddhaman` feature is retained. This is the source's represented vintage, not a guarantee of current administrative accuracy.

## Reproduction

```bash
# After restoring the reports and indexing locally:
python scripts/build_site.py
python scripts/check_browser_parity.py   # developer cases only; budget 0
pytest -q

# In another terminal:
python -m http.server 8765 --bind 127.0.0.1 --directory docs
# With Playwright 1.62.1 and Chrome installed:
node scripts/check_browser.cjs
```

CI repeats the static bundle tests and both browser checks without source PDFs or SerpApi credentials. It does not rebuild the index or invoke `eval`. CI browser reports are uploaded as run artifacts rather than replacing the frozen research results.

[Pyodide's official quickstart](https://pyodide.org/en/stable/usage/quickstart.html) lists the pinned `314.0.7` release used here. The site loads its module worker runtime from `cdn.jsdelivr.net`. Initial internet/CDN access is required, and runtime download size is additional to the reported initial-page payload.

## Limits and credits

- **Zero SerpApi credits** used. Ledger remains 211 recorded searches; this is ledger accounting, not a newly queried account balance.
- The paid-plan harvest was **skipped**: no explicit paid-plan authorisation was supplied. The map includes district boundaries without asserting new source coverage for every district.
- Hindi/Bengali support is a finite dictionary, not general translation. Unknown native-script village names stay unchanged and abstain; answers remain English with a language header.
- Abstract place linking remains heuristic and can produce non-place tokens; the UI marks study-level support and the lack of a verified site identity. Unknown publication or sampling dates remain UNKNOWN.
- No external human review, new scientific benchmark, or new harvest occurred in this round. The old limitations in `reports/holdout_audit.md` remain part of the research record.
