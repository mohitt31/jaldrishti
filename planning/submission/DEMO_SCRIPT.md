# Local functional demo

The automated recording runs the actual local static site at `http://127.0.0.1:8765/`, including the real Pyodide worker. Captions are added to explain actions; no answer, score or search result is substituted. Reviewer text is explicitly marked SCRIPTED DEMO and is not user feedback. There is no voice clone or invented testimonial.

Sequence: intended researcher/problem → measured value → row/source metadata → real saved SerpApi discovery trail → 332/329 comparison refusal → explicit curated scope → portable note → synthetic review comment → export/import/Python recheck → insufficient evidence → coverage map → claims and limits.

Recording command (Chrome and Playwright needed):

```bash
python -m http.server 8765 --bind 127.0.0.1 --directory docs
node scripts/record_demo.cjs
```

`SITE_URL` and `DEMO_OUTPUT` can change the local address/output. Keep the address local for the submitted recording. Chrome video capture produces WebM; convert with ffmpeg to H.264 MP4, retaining the recorded functionality. No video is a user timing experiment. Source availability/Python startup can change capture duration; verify the final video is strictly shorter than 180 seconds. The public demo page hosts the resulting recording without requiring an account.

After recording: inspect beginning, numeric evidence, provenance, comparison, note handoff and end frames; play the exported MP4 in a fresh browser context; check duration and seek; open the public demo page without authentication. Retain recording metadata and media SHA-256 in `reports/submission_readiness/`.
