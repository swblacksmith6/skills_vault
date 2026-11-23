---
name: analyze-and-publish
description: Analyse a folder of company filings end to end and publish the result to the user's GitHub Pages site. Runs the equity deep dive (quick scan, concall walk-the-talk, growth triggers, valuation), builds one combined HTML investment report, adds a "what changed since the last analysis" storyline when the company was covered before, stamps a non-removable educational disclaimer, updates the site index, and commits and pushes to main. Use when the user says "analyse and publish", "publish analysis for this company", "run the pipeline on this folder", "analyse this folder and put it on GitHub pages", or gives a filings folder or an Indian stock ticker and asks for the report to be online.
---

# Analyze and Publish

One folder of filings in, one live GitHub Pages report out.

## Settings (kept outside the plugin)

The plugin carries no user-specific paths or repos. They live in a settings file on the user's own computer:

`~/.config/equity-research/config.json`

```json
{
  "repo_path": "/absolute/path/to/pages-repo",
  "github_remote": "owner/repo",
  "branch": "main",
  "site_url": "https://owner.github.io/repo/",
  "filings_dir": "/absolute/path/for/downloaded/filings"
}
```

`filings_dir` is optional (screener-docs uses it as its default output folder). Below, `<repo>`, `<remote>`, `<branch>` and `<site>` mean these values, and `<repo_name>` means the last folder name of `repo_path`.

**Reading it:**
- **Native shell on the user's computer:** read the file directly.
- **Linked computer** (`mcp__remote-devices__*`): request access to `~/.config/equity-research` in the same `device_request_folder_access` call as the filings folder, then stage `config.json`.
- **Missing values:** ask for them rather than guessing.

**First run (file or folder missing):**
- Ask the user with AskUserQuestion for: the repo path, the GitHub remote, the branch (default `main`) and, optionally, the filings folder.
- Derive `site_url` as `https://<owner>.github.io/<repo>/` unless the user says the site uses a custom domain.
- Write the file:
  - **Native shell:** write it directly.
  - **Linked computer:** a new folder cannot be granted before it exists. Give the user this one command, filled in with their answers, to run once in Terminal, then continue with the values you already have:
    ```bash
    mkdir -p ~/.config/equity-research && cat > ~/.config/equity-research/config.json <<'JSON'
    { "repo_path": "...", "github_remote": "...", "branch": "main", "site_url": "...", "filings_dir": "..." }
    JSON
    ```
- Never store tokens, passwords or cookies in this file.

Filings folders usually sit under `<repo>/temp/` (ignored by git), but any folder the user names works.

`${CLAUDE_PLUGIN_ROOT}/skills/analyze-and-publish` is `SKILL_DIR` below.

## Non-negotiables

1. **Disclaimer on everything.** Every report is built with `SKILL_DIR/scripts/build_report.py`, which hard-codes a sticky red banner at the top and a red block at the bottom: *educational purpose only, not a buy or sell recommendation, act without your own research and you are guaranteed to lose your money.* Never build the report with another builder, and never remove or reword the banner. Every markdown deliverable also ends with that sentence in bold.
2. **Never fabricate.** All of equity-deep-dive's rules apply unchanged (units, page citations, verbatim guidance, TTM P/E, attribution, standalone vs consolidated).
3. **Add, never overwrite.** Earlier analyses stay in the repo untouched. A re-analysis adds new dated files next to the old ones.
4. **Commit only what this run produced**, plus `index.html` and `.gitignore`. Never `git add .` (the `temp/` folder holds raw PDFs).
5. Pushing straight to `main` is pre-approved by the user. No need to ask before pushing.

## Workflow

Create a task list with these steps and tick them off.

### 1 · Locate inputs and the repo

- Load the settings (above).
- Get the filings folder path from the user's message.
  - **Ticker or company name instead of a folder:** run the **screener-docs** skill first to download the filings, then use its `<out>/<SYMBOL>` folder.
- **Linked computer** (`mcp__remote-devices__*`): request access to the repo and the filings folder in as few `device_request_folder_access` calls as possible. Skip the filings folder if it is inside the repo. The repo path comes from the settings, so the settings read may need its own call first.
- **Native shell** (Claude Code): use the paths directly.
- Work in a scratch directory in the workspace (`work/<TICKER>/`). Stage filings in with `device_stage_files` when they live on the device, or read them in place with a native shell.
- Settle the **company display name** and **ticker** from filenames, first pages or the user. They drive folder and file naming.

### 2 · Find the previous analysis

```bash
python3 SKILL_DIR/scripts/repo_tool.py find-prior --repo <repo> --company "<Display Name>" --ticker <TICKER>
```

Run it against the repo (in `device_bash` the repo is at `$HOME/mnt/<repo_name>`; copy `repo_tool.py` there first or stage `index.html` and the folder listing into the workspace).

- **Found:** reuse its `folder` and `ticker_prefix` for naming. Read the newest dated files (and any undated ones) and pull out the **prior snapshot** described in `references/storyline.md`. The whole report then gets the storyline treatment.
- **Not found:** new company. Folder = full company name (e.g. `Kaynes Technology India Ltd`). Prefix = NSE symbol.

### 3 · Run the analysis (equity-deep-dive)

Load the `equity-deep-dive` skill with the Skill tool and run its **full pipeline, Steps 1–6**: triage (show the manifest and gaps), extract, fan-out extraction, market data, the four analyses, and the mandatory adversarial verification. Adjustments:

- Name outputs `<PREFIX>_quick_scan_<YYYYMMDD>.md`, `<PREFIX>_walk_the_talk_<YYYYMMDD>.md`, `<PREFIX>_growth_triggers_<YYYYMMDD>.md`, `<PREFIX>_valuation_<YYYYMMDD>.md`, using today's date.
- Keep the headings that the investment-report-html skill parses: the 12-point AR analysis, the 10-point Forensic Red Flag Scan, Piotroski F-Score, DuPont, Bear case; headline numbers, guidance with HIGH/MEDIUM/LOW confidence, the Walk-the-Talk scorecard; the Trigger Scoreboard with conviction and ₹ cr quantum, Risks; Base/Bull/Bear vs CMP.
- **If a prior analysis exists:** give the verification subagent the prior snapshot too, so it checks the Then-vs-Now numbers. End each of the four markdowns with a `## Changes since the <DD Mon YYYY> analysis` section, and write a fifth file, `<PREFIX>_storyline_<YYYYMMDD>.md`, per `references/storyline.md`.
- **Skip** equity-deep-dive's Steps 7–8 (its own report and delivery). This plugin builds the report and handles publishing. Its Step 9 memory note is still worth writing.

Send each markdown to the user with SendUserFile as it is finished.

### 4 · Build the combined HTML report

Read `references/report-sections.md`. It merges equity-deep-dive's report contract with every section investment-report-html requires, and adds the storyline and valuation sections. Write `report.json`, then:

```bash
python3 SKILL_DIR/scripts/build_report.py report.json --out <PREFIX>_report_<YYYYMMDD>.html
python3 SKILL_DIR/scripts/check_report.py <PREFIX>_report_<YYYYMMDD>.html --shot shot.png
```

Fix anything `check_report.py` flags, then look at the screenshot. The red banner must be visible at the top.

### 5 · Publish

Follow `references/publishing.md`. It picks the push route for the environment you are running in. In short: run

```bash
python3 repo_tool.py publish --repo <repo> --folder "<Folder>" --company "<Display Name>" --date <YYYYMMDD> --files <all md + html> --commit --message "<Display Name>: analysis <DD Mon YYYY>"
```

then push `main`.

### 6 · Deliver

- Report link: `<site><url-encoded folder>/<PREFIX>_report_<YYYYMMDD>.html`. Pages takes about a minute to rebuild, so say so.
- SendUserFile the HTML report.
- In prose: the verdict, the two or three facts that drive it, how the thesis and valuation moved since last time (if re-analysed), and the dated checkpoints. Don't recap the pipeline.

## Reference index

| File | Read when |
|---|---|
| `references/storyline.md` | Step 2 (prior snapshot) and Step 3 (storyline file) when the company was covered before |
| `references/report-sections.md` | Step 4: the section-by-section contract for `report.json` |
| `references/publishing.md` | Step 5: environment detection, commit and push routes, failure handling |
| `scripts/repo_tool.py` | find-prior / publish / gitignore |
| `scripts/build_report.py` | The only report builder to use (disclaimer baked in) |
| `scripts/inject_disclaimer.py` | Retrofit the banner onto older HTML reports or layouts |
