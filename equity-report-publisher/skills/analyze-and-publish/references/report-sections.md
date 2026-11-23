# Combined report: `report.json` contract

Schema and block types are exactly those of equity-deep-dive's `references/13-report-schema.md` (load that file from the equity-deep-dive skill directory). This plugin's `build_report.py` is a copy of that builder with two additions:

- A sticky red **disclaimer banner** at the top and a red block before the footer. Both are hard-coded and need nothing in `report.json`.
- `meta.previous`: `[{"label": "30 Jun 2026", "href": "GRAVITA_report_20260630.html"}]`. This renders an "Earlier analyses" strip in the header. The hrefs are relative, since files sit in the same folder.

The content requirements below combine the investment-report-html skill's checklist with the deep dive's structure. Every item is required when the source markdown has the data. If it doesn't, show `n/a`. Never interpolate.

## Order of the page

1. **Header**: company, exchange/ticker, sector, report date, verdict badge (green BUY-WORTHY / amber WATCH / red PASS), kv tiles for CMP, Mcap, TTM P/E, 52-week range, plus `price_note` with the source and as-of date, and `meta.previous`.
2. **Executive summary card**: verdict + one-line business description, then the 2–3 facts that drive it. For a re-analysis, add one line: "Since <date>: <verdict then> → <verdict now>; Base fair value ₹a → ₹b".
3. **Stat tiles (4–6)**: Piotroski (`bar` = score/9×100), management credibility (HIGH/MEDIUM/LOW, with hit rate), trigger counts (HIGH / MEDIUM / OPTIONALITY), Base-case upside vs CMP, and CFO/PAT conversion.
4. **"The one thing to check" callout** (amber).
5. **Section 0 · Storyline since <DD Mon YYYY>** (re-analysis only; see `storyline.md`):
   - Then-vs-now table with a `Change` column, tinted green/red by direction
   - `charts2`: (a) **valuation then vs now**, grouped bars for Bear/Base/Bull at both dates, with CMP at both dates as a line dataset; (b) the running Walk-the-Talk credibility total across both analyses
   - Trigger tracker table with a status tag (`PLAYED OUT` green, `IN PROGRESS` amber, `DELAYED` amber, `BROKEN` red, `DROPPED SILENTLY` red)
   - Promise tracker table
   - `columns2` callouts: "Thesis then" (grey) | "Thesis now" (green/amber/red by verdict), and below them "Why the valuation moved"
6. **1 · Company Quick Scan**
   - 12-point AR analysis → 2-column table
   - 10-point Forensic Red Flag Scan → table, rating cell tinted GREEN/AMBER/RED
   - Piotroski F-Score → stat tile or a horizontal 0–9 bar chart, with the 9 tests as a small table
   - DuPont (net margin, asset turnover, leverage, ROE) → grouped bar chart over 3 years, with mixed units noted
   - Reported PAT vs operating cash flow chart (the most important chart)
   - Segment revenue (stacked) if disclosed
   - Bear case → red callout
7. **2 · Concall and Walk-the-Talk**
   - Headline numbers table (Revenue, EBITDA, PAT, margin; QoQ and YoY) with ▲ (green) / ▼ (red) in the change cells
   - Revenue / EBITDA / PAT line chart across available quarters
   - Guidance table: verbatim statement, source, period, confidence tint HIGH green / MEDIUM amber / LOW red
   - Walk-the-Talk scorecard: per-promise beat +1 / miss −1 bars with the running total on a second axis; credibility rating stated
8. **3 · Growth triggers**
   - Trigger Scoreboard: conviction tag HIGH green / MEDIUM amber / OPTIONALITY grey, with quantum (₹ cr), timeline and evidence
   - Horizontal bar chart of quantum per trigger, coloured by conviction
   - Risks → red callout list
9. **4 · Valuation**
   - Scenario table: Bear / Base / Bull with key assumptions (revenue, margin, EPS, multiple), fair value and gap vs CMP (tinted)
   - Bar chart of the three fair values against a CMP line
   - Note how the credibility rating discounted guidance in the Bull case
10. **5 · Verdict and checkpoints**: `columns2` with "What would upgrade" (green) | "What would downgrade" (red), then a dated checkpoints table and follow-up questions.
11. **Raw markdown** collapsibles (`raw` with `file` entries), one per markdown produced this run (storyline first if present). `raw_title`: "Full source analyses".
12. **Footer**: generated timestamp, source documents consumed, method (SOIC frameworks via equity-deep-dive; verified by an independent pass), and `disclaimer`: "<b>Educational purpose only. Not a buy or sell recommendation.</b>"

## Charts

Palette: green `#16a34a`, amber `#d97706`, red `#dc2626`, grey `#6b7280`, blue `#93c5fd`. Aim for 6–9 charts (8 including the storyline pair is fine). Every chart needs a title with units.

## Before building

- Every number in `report.json` must appear in one of the verified markdowns. The report is a rendering, not a new analysis.
- Keep citations visible: put `cite` on table cells and `cite` on tables.
- Run `check_report.py`. It fails on console errors, charts that never drew and empty collapsibles.
