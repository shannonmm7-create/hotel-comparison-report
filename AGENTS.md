# Agent guide — Hotel Comparison Report

This is the **canonical** instruction file for AI coding agents (Claude Code,
GitHub Copilot, OpenAI Codex). `.github/copilot-instructions.md`, `CLAUDE.md`, and
`.claude/skills/hotel-comparison-report/SKILL.md` all point here so every agent
behaves identically.

## What this repo does

Renders the **JC Room Blocks Hotel Comparison Report** `.docx` from a JSON data
file by filling an approved Word template with [docxtpl](https://docxtpl.readthedocs.io/).
You assemble the JSON; the tool does all formatting. **Never build or hand-edit
the `.docx` yourself.**

## Golden rules

1. **Always run through `uv`.** It pins the exact dependency versions (a committed
   `uv.lock`), so behavior is identical on macOS/Windows/Linux. Never
   `pip install` or call `python` directly for the CLI.
2. **The JSON Schema is the contract.** The data must match
   `src/hotel_report/schema/report.schema.json`. Validate before rendering. Do not invent fields
   (`additionalProperties` is `false`).
3. **Don't touch the `.docx` by hand.** To change the *layout*, edit the source
   (`assets/source_template.docx`) and regenerate via `build-template`. To change
   *content*, change the data JSON.
4. **Editing the engine?** Read `docs/docx-templating-notes.md` first — the
   OOXML/docxtpl gotchas there are not obvious and will bite you.

## The task: produce a report

```bash
uv sync                                                 # once, installs locked deps

# 1. get the data contract / a starting point
uv run hotel-report schema                              # the JSON Schema
uv run hotel-report example my_report.json             # a filled-in example to adapt

# 2. write my_report.json (see "Data shape" below), then check it
uv run hotel-report validate my_report.json

# 3. render
uv run hotel-report render my_report.json report.docx
```

`render` re-validates by default and fails if any template token survives.

## Data shape (summary — schema is authoritative)

Top level: `prepared_for`, `arrival_date`, `departure_date`, `venue_name`,
`hotels[]`. Each hotel: `name` (+ optional `website_url` → name becomes a link),
`address_line_1`, `city_state_zip`, optional `tripadvisor{text,url}`,
`rooms[]{room_type, offered_rate, rack_rate}` (one rate-table row each),
`features[]` / `concessions[]` / `contracting_options[]` (free bullet lists, any
length), `distance_from_venue` (number only; template adds " miles"), `cutoff`
(e.g. "30 days"; template adds " prior to arrival"). Rates may be numbers
(rendered `$1,250`) or strings (`"Waived"`).

> **Data acquisition is out of scope right now.** This repo proves the templating
> is correct and deterministic. A future pipeline's only job is to emit JSON that
> satisfies the schema — the engine won't change.

## Tests & CI

```bash
uv run pytest          # schema + render + build-template tests
uv run ruff check .    # lint
```

CI (`.github/workflows/ci.yml`) runs both on every push/PR. Keep them green.

## Where things live

- `src/hotel_report/cli.py` — the `hotel-report` command
- `src/hotel_report/render.py` — docxtpl fill, currency, RichText hyperlinks
- `src/hotel_report/build_template.py` — source `.docx` → Jinja template
- `src/hotel_report/schema.py` + `src/hotel_report/schema/report.schema.json` — the contract
- `docs/docx-templating-notes.md` — **read before editing the engine**
