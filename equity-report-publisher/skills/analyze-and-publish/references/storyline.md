# Storyline: re-analysing a company covered before

The point of a re-analysis is the **story over time**: what we believed on the earlier date, what has actually happened since, and how the thesis and valuation moved. A reader should be able to see in one screen whether the company did what it said it would.

## 1 · Build the prior snapshot (Step 2)

From the newest earlier analysis in the repo (`find-prior` → `latest_date`), extract the fields below. Earlier analyses vary in format: some lack a valuation file, some have undated walk-the-talk files. If a field is absent, record `not analysed then`. Never back-fill it from memory or from today's data.

| Field | Where it usually lives |
|---|---|
| Analysis date | filename date (or the report header) |
| CMP and Mcap on that date | quick scan header |
| Verdict (BUY-WORTHY / WATCH / PASS) | quick scan verdict |
| Piotroski score | quick scan |
| Forensic flags rated RED | quick scan red-flag table |
| Management credibility (HIGH/MEDIUM/LOW) and hit rate | walk-the-talk |
| Guidance statements (verbatim, with the period they referred to) | walk-the-talk |
| Growth triggers with conviction and quantum | growth triggers scoreboard |
| Bear / Base / Bull fair value and the implied upside vs that day's CMP | valuation file |
| Key risks / bear case | quick scan, growth triggers |
| Dated checkpoints named then | verdict / follow-up sections |

Keep the snapshot in `work/<TICKER>/prior_snapshot.md` with a source file for every line.

## 2 · Compare (Step 3)

For each prior item, decide its status using **today's filings only**:

- **Triggers:** `PLAYED OUT` / `IN PROGRESS` / `DELAYED` / `BROKEN` / `DROPPED SILENTLY` (the company stopped mentioning it). Cite the evidence for each.
- **Guidance promises** whose period has now passed: `BEAT` / `MET` / `MISSED`, with the actual number. These feed the running Walk-the-Talk score across both analyses.
- **Red flags:** `RESOLVED` / `PERSISTS` / `WORSENED`, plus any **new** flags.
- **Valuation:** old Bear/Base/Bull vs new Bear/Base/Bull, old CMP vs new CMP. Explain each change in fair value: is it earnings revision, multiple change, or a trigger moving between scenarios? Price moves and value moves are different things, so say which one happened.
- **Verdict:** old → new, with the one-sentence reason it changed or held.

## 3 · `<PREFIX>_storyline_<YYYYMMDD>.md`

```markdown
# <Company> — What changed since the <DD Mon YYYY> analysis

**Previous analysis:** <DD Mon YYYY> (CMP ₹x, verdict X) · **This analysis:** <DD Mon YYYY> (CMP ₹y, verdict Y)

## The story so far
3–6 sentences in plain language: what the thesis was, what happened, where it stands now.

## Then vs now
| Metric | <old date> | <new date> | Change |
(CMP, Mcap, verdict, Piotroski, credibility, Bear/Base/Bull fair value, upside to Base, TTM revenue/PAT, CFO)

## Trigger tracker
| Trigger (as stated then) | Conviction then | Status now | Evidence |

## Promise tracker (guidance whose period has passed)
| Promise (verbatim, source) | Period | Actual | Result |

## Red flags: then vs now

## Investment thesis evolution
- **Then:** …
- **Now:** …
- **Valuation shift:** why the fair value moved (earnings / multiple / scenario mix)
- **What would change our view next:** dated checkpoints

**Educational purpose only — not a buy or sell recommendation. If you act on this without doing your own research, you are guaranteed to lose your money.**
```

## 4 · In the HTML report

The storyline becomes section **0** (see `report-sections.md`), placed straight after the stat tiles so it sits above the fold. The header's `meta.previous` lists every earlier report in the folder as a link.
