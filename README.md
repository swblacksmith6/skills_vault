# Skills Vault

A collection of skills for OpenClaw. Each skill lives in its own folder with a `SKILL.md` that defines when and how it is used.

## Index

| Skill | Description | Requires |
|---|---|---|
| [screener-docs](screener-docs/SKILL.md) | Download a listed Indian company's annual reports, concall transcripts, investor presentations and credit rating reports from screener.in into a local folder. | `python3` (deps installed by `run.sh` via `uv` or a managed venv) |
| [equity-report-publisher](equity-report-publisher/skills/analyze-and-publish/SKILL.md) | Plugin: bundles screener-docs plus analyze-and-publish. From a ticker or a filings folder, runs equity-deep-dive, builds a combined HTML report (storyline for repeat companies, educational disclaimer) and publishes it to your GitHub Pages site. Repo and site are read from `~/.config/equity-research/config.json`, never stored in the plugin. Install via `equity-report-publisher.plugin`. | `equity-deep-dive` skill, `python3`, `git` |

## Layout

```
skills_vault/
  README.md
  <skill-name>/
    SKILL.md        skill definition (frontmatter + instructions)
    scripts/        helper scripts used by the skill
```

## License

Released under the [MIT License](LICENSE).

## Adding a skill

1. Create a folder named after the skill.
2. Add a `SKILL.md` with `name`, `description` and `metadata` frontmatter, followed by the workflow.
3. Put any scripts under `scripts/`.
4. Add a row to the index table above.
