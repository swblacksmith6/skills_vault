# Publishing to GitHub Pages

The commit always happens in the user's real clone at `<repo>` (from the settings file), so the user's computer stays the single source of truth. Only the push route depends on where this session runs.

## Detect the environment

| Check | Route |
|---|---|
| `git -C <repo> status` works in the native Bash tool (Claude Code on the user's computer) | **A · Native** |
| `mcp__remote-devices__device_bash` is available (Claude app linked to the user's computer) | **B · Linked computer** |
| Neither | Stop and ask the user to open the chat in the Claude desktop app on the computer that holds the repo, or to run from Claude Code |

## A · Native shell (Claude Code on the user's computer)

The user's own git credentials work here.

```bash
cd <repo>
git pull --ff-only
python3 SKILL_DIR/scripts/repo_tool.py publish --repo . --folder "<Folder>" --company "<Name>" \
  --date <YYYYMMDD> --files <work>/<PREFIX>_*_<YYYYMMDD>.* --commit --message "<Name>: analysis <DD Mon YYYY>"
git push origin <branch>
```

## B · Claude app linked to the user's computer

The device shell is a sandbox. It can read, commit, clone and fetch, but **GitHub pushes from it are blocked**, and the user's keychain credentials are not visible to it. Terminal apps are click-only for computer use, so a push can't be typed there either.

1. **Access:** one `device_request_folder_access` for the repo (plus the filings folder if it is outside it). Then one `device_request_delete_permission` for the repo, because git must delete its own `.lock` files to commit. Ask for both once per session.
2. **Get the tools onto the device:** copy `repo_tool.py` into `<repo>/temp/_tools/` (git ignores `temp/`). Write it to `/mnt/user-data/outputs/` and send it across with `device_commit_files`. Do the same with the finished `.md`/`.html` files, into `<repo>/temp/_publish/<PREFIX>_<YYYYMMDD>/`.
3. **Commit on the device** (`$HOME/mnt/<repo_name>` inside `device_bash`):
   ```bash
   cd $HOME/mnt/<repo_name> && rm -f .git/*.lock && git pull --ff-only
   python3 temp/_tools/repo_tool.py publish --repo . --folder "<Folder>" --company "<Name>" \
     --date <YYYYMMDD> --files temp/_publish/<PREFIX>_<YYYYMMDD>/* --commit --message "..."
   ```
   `repo_tool.py` reuses the last commit's author if git has no identity configured.
4. **Push.** Try these in order:
   - **B1 · Cloud push** (works once the Claude GitHub App is installed on `<remote>`): call `mcp__claude-code-remote__add_repo` with `access: "push"`. If its `push_check` is not `refused`:
     ```bash
     # device: bundle exactly the new commits (same hashes, so no divergence later)
     cd $HOME/mnt/<repo_name> && git bundle create temp/_publish/push.bundle origin/<branch>..<branch>
     ```
     Stage the bundle with `device_stage_files`, then in the workspace:
     ```bash
     git clone --depth 1 https://github.com/<remote> /home/claude/<repo_name>   # if not cloned yet
     cd /home/claude/<repo_name> && git fetch /mnt/user-data/uploads/<repo_name>/temp/_publish/push.bundle <branch>:publish
     git -c push.negotiate=true push origin publish:<branch>
     ```
     Then on the device run `git fetch -q && git status -sb`. It should say `<branch>...origin/<branch>` with nothing ahead.
   - **B2 · Hand the push to the user** if B1 is refused. Don't retry other routes, and don't try to type into Terminal through some other app. Tell the user, with the command in a code block:
     `git -C <repo> push origin <branch>`
     Also mention once that installing the Claude GitHub App on the repo lets future runs push on their own: https://github.com/apps/claude/installations/select_target

## After pushing

- Pages rebuilds in about a minute. The report URL is `<site>` + URL-encoded folder + `/` + report filename.
- If the push was rejected as non-fast-forward, run `git pull --rebase` on the device (or in the native shell) and push again. Never force-push.
- Leave the files in `temp/_publish/` (git ignores them) unless the user asks for a cleanup.
