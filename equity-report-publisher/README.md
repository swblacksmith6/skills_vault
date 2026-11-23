# equity-report-publisher

From an Indian stock ticker, or a folder of company filings, to a live, disclaimer-stamped investment report on your GitHub Pages site.

**Ask:**
- "Download TCS filings from screener" (fetch only)
- "Analyse and publish TCS" (fetch, analyse, publish)
- "Analyse and publish `<path to a filings folder>`" (analyse and publish existing files)

## Skills

### screener-docs
Finds the company on screener.in and downloads the documents its page links to:

| Category | Up to |
|---|---|
| Annual reports | 3 |
| Concall transcripts | 12 |
| Investor presentations | 12 |
| Credit rating reports | 3 |

Screener is used only to find the links. The files come from BSE, NSE and the rating agencies. A `manifest.json` records every file's source and status.

### analyze-and-publish
1. Downloads the filings first with screener-docs when given a ticker.
2. Checks whether the company was analysed before, using the site index and the repo folders.
3. Runs the **equity-deep-dive** pipeline: triage, extraction, quick scan, concall walk-the-talk, growth triggers, valuation, and adversarial verification.
4. For a repeat company, adds a **storyline**: what changed since the last analysis.
5. Builds one offline HTML report. The builder hard-codes a sticky red **"Educational purpose only, not a buy/sell recommendation"** banner.
6. Copies the files into your repo, updates `index.html`, commits only those files, and pushes.

## Settings

Nothing user-specific is stored in the plugin. On first use it asks for your settings and saves them on your computer at `~/.config/equity-research/config.json`:

```json
{
  "repo_path": "/absolute/path/to/your/pages-repo",
  "github_remote": "owner/repo",
  "branch": "main",
  "site_url": "https://owner.github.io/repo/",
  "filings_dir": "/optional/folder/for/downloads"
}
```

Edit that file to point the plugin at a different repo.

## Requirements

- **Skills installed:** `equity-deep-dive`.
- **Software:** `python3` and `git`. screener-docs installs `requests` and `beautifulsoup4` into its own isolated environment, using `uv` if present.
- **Network:** access to `www.screener.in` and `www.bseindia.com`. If a Claude session's network allowlist blocks screener.in, the skill gives you the one command to run in your own terminal.
- **Pushing:**
  - From Claude Code on your computer, pushing works by itself.
  - From the Claude app, it works by itself once the Claude GitHub App is installed on your repo.
  - Otherwise the final `git push` is handed to you as one command.

## Files

- `skills/screener-docs/`: `SKILL.md`, `scripts/screener_docs.py`, `scripts/run.sh` (isolated-env launcher)
- `skills/analyze-and-publish/SKILL.md`: the workflow and settings
- `skills/analyze-and-publish/references/`: storyline method, report section contract, publishing routes
- `skills/analyze-and-publish/scripts/repo_tool.py`: find prior analysis, publish and update the index, .gitignore
- `skills/analyze-and-publish/scripts/build_report.py`, `assets/`: report builder with the disclaimer banner (Chart.js inlined, MIT)
- `skills/analyze-and-publish/scripts/check_report.py`: headless render check
- `skills/analyze-and-publish/scripts/inject_disclaimer.py`: retrofit the banner onto older HTML
