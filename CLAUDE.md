# CLAUDE.md

The full agent guide is **[`AGENTS.md`](AGENTS.md)** — read it. There is also a
Claude skill at `.claude/skills/hotel-comparison-report/SKILL.md`.

Essentials:

- This repo renders the JC Room Blocks Hotel Comparison Report `.docx` by filling
  an approved template with docxtpl. **You assemble JSON only — never build or
  hand-edit the `.docx`.**
- **Always run through `uv`** (locked deps, cross-platform):
  `uv run hotel-report render <data.json> <out.docx>`.
- Data must match `src/hotel_report/schema/report.schema.json`; validate before rendering
  (`uv run hotel-report validate <data.json>`).
- Keep `uv run pytest` and `uv run ruff check .` green.
- **Before editing `render.py` / `build_template.py`, read
  [`docs/docx-templating-notes.md`](docs/docx-templating-notes.md)** — the
  python-docx / docxtpl gotchas there are load-bearing.
