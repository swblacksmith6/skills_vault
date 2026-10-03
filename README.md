# Skills Vault

A collection of skills for OpenClaw. Each skill lives in its own folder with a `SKILL.md` that defines when and how it is used.

## Index

| Skill | Description | Requires |
|---|---|---|
| [screener-docs](screener-docs/SKILL.md) | Download a listed Indian company's annual reports, concall transcripts, investor presentations and credit rating reports from screener.in into a local folder. | `python3`, `requests`, `beautifulsoup4` |

## Layout

```
skills_vault/
  README.md
  <skill-name>/
    SKILL.md        skill definition (frontmatter + instructions)
    scripts/        helper scripts used by the skill
```

## Adding a skill

1. Create a folder named after the skill.
2. Add a `SKILL.md` with `name`, `description` and `metadata` frontmatter, followed by the workflow.
3. Put any scripts under `scripts/`.
4. Add a row to the index table above.
