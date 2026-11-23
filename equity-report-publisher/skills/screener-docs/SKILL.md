---
name: screener-docs
description: Download a listed Indian company's documents from screener.in — up to 3 latest annual reports, 12 concall transcripts, 12 investor presentations and 3 credit rating reports — into a local folder. Use whenever the user names a stock/company/ticker (e.g. "TCS", "Tata Motors", "Dixon") and asks to fetch, download, pull, gather or collect its annual reports, concall transcripts, investor presentations (PPTs) or credit ratings, or mentions screener.in documents. Also the gather step when analyze-and-publish is given a ticker instead of a folder.
---

# Screener.in Document Downloader

Find the company on screener.in, read the links in the **Documents** section of its page, and download the files those links point to. The files themselves are hosted by the exchanges (mostly BSE, sometimes NSE) and by the rating agencies. Screener only provides the search results and the list of links.

`SKILL_DIR` below is this skill's folder (`${CLAUDE_PLUGIN_ROOT}/skills/screener-docs`).

## What gets downloaded (newest first)

| Category | Default max | File |
|---|---|---|
| Annual reports | 3 | `annual_reports/AR_FY2025.pdf` |
| Concall transcripts | 12 | `concall_transcripts/Transcript_2025-07.pdf` |
| Investor presentations | 12 | `investor_presentations/PPT_2025-07.pdf` |
| Credit rating reports | 3 | `credit_ratings/2025-06-03_icra.pdf` (some agencies serve `.html`) |

Output layout: `<out>/<SYMBOL>/<category>/...` plus `<out>/<SYMBOL>/manifest.json` (source URL and status for every file).

**Date naming:** `Transcript_YYYY-MM` and `PPT_YYYY-MM` carry the month the document was **filed**, not the quarter it covers. A file dated `2026-11` usually covers the quarter ended September (Q2). Read the document's first page for the actual period before labelling it, and tell downstream analysis to do the same.

## Where to run it

The script needs to reach `www.screener.in`, `www.bseindia.com` and, for some companies, `www.nseindia.com` and the rating-agency sites. Pick the first route that works:

1. **Native shell on the user's machine** (Claude Code): run it directly.
2. **Linked computer shell** (`mcp__remote-devices__device_bash`): run it there, writing into a connected folder.
3. **The cloud workspace shell.**

Test once with `curl -sS -o /dev/null -w "%{http_code}" https://www.screener.in/`. If every available shell is blocked (a proxy 403 or connection refused), do not try other download routes. Tell the user that screener.in is not on this session's network allowlist. Then give them the exact command to run in their own terminal (step 3 below) and continue once the files are in a folder you can read.

## Output folder

1. Use the folder the user names.
2. Otherwise use `filings_dir` from the settings file `~/.config/equity-research/config.json`, if it exists and is readable (see analyze-and-publish's settings section).
3. Otherwise use `~/screener_docs`.

## Workflow

1. **Launcher.** Use `SKILL_DIR/scripts/run.sh`. It runs the script in an isolated Python environment: `SCREENER_DOCS_PYTHON` if set, else `uv run --script` (dependencies are declared inline), else a managed venv under `${XDG_STATE_HOME:-~/.local/state}/screener-docs/venv`. On a machine where `run.sh` cannot be used, run `python3 SKILL_DIR/scripts/screener_docs.py` after `python3 -m pip install requests beautifulsoup4` (add `--break-system-packages` in the cloud workspace).
   - If the plugin folder is not reachable from the shell you are using (for example the linked computer's shell), copy `screener_docs.py` and `run.sh` into a scratch folder there first.

2. **Confirm the company if the name is ambiguous.** For names like "HDFC", "Tata", "Adani" or "Bajaj", list matches first:
   ```bash
   bash SKILL_DIR/scripts/run.sh "HDFC" --list-matches
   ```
   Show the list and ask which one, unless one match is clearly what the user meant. A plain NSE symbol (`TCS`, `DIXON`) or a screener URL is usually unambiguous.

3. **Download:**
   ```bash
   bash SKILL_DIR/scripts/run.sh "<stock name or symbol>" --out "<output folder>" [--pick N]
   ```
   Useful flags:
   - `--pick N`: use the Nth search match.
   - `--dry-run`: list what would be downloaded without downloading.
   - `--max-ar`, `--max-transcripts`, `--max-ppts`, `--max-ratings`: override limits.
   - Pass a full URL (e.g. `https://www.screener.in/company/TCS/consolidated/`) to skip search.

   Re-running is safe: already-downloaded files are skipped.

4. **Report back:**
   - the save folder;
   - counts per category from the script's summary;
   - any failed items (from `manifest.json`).

   Do not paste the whole manifest. If analyze-and-publish called this skill, hand it the `<out>/<SYMBOL>` folder and continue.

## Notes and troubleshooting

- "Maximum" means *up to*. A recently listed company has only one or two annual reports, and many companies have no credit rating. That is normal; report what was found and say why a category is empty where it is obvious (for example, a listing date this year).
- The script sends a `Referer` header matching the host (BSE, NSE or screener.in). If many BSE/NSE downloads fail with 403, retry later with a larger `--delay` (e.g. `--delay 3`).
- Status `warning: tiny html` means the source returned a stub page instead of the document. Mention it and give the user the source URL from the manifest.
- If screener starts requiring login, the user can export their `sessionid` cookie as `SCREENER_SESSIONID` before running. Never ask the user to paste the cookie into chat, and never type it yourself.
- If the parse finds 0 items in every category, screener's page layout may have changed. Fetch the page, inspect the `#documents` section, and update the selectors in `parse_documents()` (`div.annual-reports`, `div.credit-ratings`, `div.concalls`).
- Be polite to screener.in: never loop over large stock lists without a delay.
