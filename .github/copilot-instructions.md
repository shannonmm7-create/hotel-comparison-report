# GitHub Copilot instructions

This project has one canonical agent guide: **[`AGENTS.md`](../AGENTS.md)**. Follow
it. Summary so you don't go off-script:

- Render the Hotel Comparison Report by filling an approved Word template with
  [docxtpl](https://docxtpl.readthedocs.io/). **Never build or hand-edit the
  `.docx`.** You only assemble JSON.
- **Always use `uv`** (locked, cross-platform). Don't `pip install` or call
  `python` directly for the CLI.
- The data must match `src/hotel_report/schema/report.schema.json` (`additionalProperties: false`
  — no invented fields). Validate before rendering.

Do the work:

```bash
uv sync
uv run hotel-report example my_report.json     # starting point
uv run hotel-report validate my_report.json    # check the contract
uv run hotel-report render my_report.json report.docx
uv run pytest && uv run ruff check .           # keep green
```

Before editing `render.py` or `build_template.py`, read
[`docs/docx-templating-notes.md`](../docs/docx-templating-notes.md) — the
python-docx / docxtpl gotchas there are not obvious.
