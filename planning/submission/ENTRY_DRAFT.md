# Submission text: NeerTathya

Copy-ready. Fill the participant-only fields yourself (identity, eligibility, team, how you heard, agreements).

## Project name
NeerTathya

## Track
Knowledge & Public Interest

## Tagline (one line)
Cited groundwater arsenic and fluoride evidence for West Bengal: the exact number with its source row, or a reasoned refusal.

## Description
West Bengal has some of the world's worst groundwater arsenic, and parts of the state have high fluoride. The measurements exist, but they sit in annexure tables of 100–270 page government reports and in paper abstracts. Search engines find pages about arsenic, not the row that answers a question. And the most common mistake is not a missing number but a bad comparison: one well's maximum against a district mean, or two different wells read as a trend.

NeerTathya answers a question with the exact value, unit, place, sampling period, document, page and table row. It re-reads each cited number on the source page before showing it. When two values cannot be compared (different wells, statistics, spatial support or periods) it says "not comparable" and lists the failed checks; when the sources do not support an answer it says so instead of guessing. The real Python engine runs in the browser, with a district evidence map, Hindi/Bengali questions and exportable research notes.

## How SerpApi is used
- Google Search and Google Scholar searches over 13 arsenic and fluoride districts build the evidence library: CGWB and ADB reports from Google, research papers from Scholar resolved to PubMed abstracts. Several phrasings per district, because results for these queries are erratic.
- Question-time fallback: when a source is missing, the planner turns cues in the question into one targeted search (named study → Scholar with year filters, publisher → site filter, village → quoted place name, with district resolution).
- Every response is cached by its request parameters and logged in a credit ledger, so the evaluation replays without an API key, and every answer can show which query found its document.
- A weekly scheduled GitHub Action runs three searches and lists new trusted West Bengal reports not yet in the library, for human review.

## Results
- Frozen test, 20 questions run once: 12/20, versus 2/20 for googling the question as typed; 9 searches instead of 58 (plus a one-off 56-search harvest).
- Fresh holdout of new places, written after a code freeze and run once: 17/20.
- Every cited number was re-found on its cited PDF page.
- Evidence library: 4,025 measurement records from 16 source documents across 21 districts.
- Compared with public AI assistants on six source-checked tasks: given only the report title with web search, two assistants got 0/6 because neither could reach the annexure table; given the PDF, they got 6/6. Finding the source is the hard part, which is what the SerpApi library does.
- Benchmark of 60 facts, each checked against its source page, committed before the system was built. Failures and post-hoc fixes are published.

Limits: no user study or expert review yet; the holdout was written by an AI assistant after the freeze; the library misses one newer Purulia report. Not a household safety tool.

## Links
- App: https://mohitt31.github.io/jaldrishti/
- Code: https://github.com/mohitt31/jaldrishti
- Demo video: (YouTube/unlisted link)
- Claims and evidence: https://mohitt31.github.io/jaldrishti/review.html

## AI tools used
I chose the problem, set the evaluation design and freeze rules, and decided what to keep or drop. Claude (Anthropic) built the core engine, SerpApi planner, harvest, scorer and first evaluations; ChatGPT helped research the problem and drafted the benchmark facts, which were checked against source pages; OpenAI Codex built the later fixes, the browser app, map, notes and the holdout set (authored after the freeze, which limits its independence). The demo narration is an open-source text-to-speech voice (Kokoro). No language model runs at answer time.
