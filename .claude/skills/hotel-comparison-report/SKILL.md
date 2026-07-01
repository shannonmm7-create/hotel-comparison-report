---
name: hotel-comparison-report
description: Generate the JC Room Blocks Hotel Comparison Report (.docx) from JSON data by filling an approved Word template with docxtpl. Use when asked to build, render, or produce a hotel comparison report, room-block report, or fill the JC hotel template. Assembles a validated JSON file and runs the uv-based CLI; never hand-builds the .docx.
---

# Hotel Comparison Report

Render the JC Room Blocks Hotel Comparison Report `.docx` by filling an approved
Word template. Your job is to produce a **JSON data file** and run the CLI — the
tool owns all formatting. **Never build or hand-edit the `.docx`.**

Full guide: [`AGENTS.md`](../../../AGENTS.md). Engine internals & docx gotchas:
[`docs/docx-templating-notes.md`](../../../docs/docx-templating-notes.md).

## Workflow

1. **Sync once:** `uv sync` (installs the locked dependencies).
2. **See the contract:** `uv run hotel-report schema` (JSON Schema) and
   `uv run hotel-report example my_report.json` (a complete example to adapt).
3. **Write the data JSON.** Match `src/hotel_report/schema/report.schema.json` exactly — no extra
   fields. Shape: top-level `prepared_for`, `arrival_date`, `departure_date`,
   `venue_name`, `hotels[]`; each hotel has `name` (+ optional `website_url`),
   `address_line_1`, `city_state_zip`, optional `tripadvisor{text,url}`,
   `rooms[]{room_type,offered_rate,rack_rate}`, and free-form `features[]` /
   `concessions[]` / `contracting_options[]` bullet lists, plus
   `distance_from_venue` and `cutoff`.
4. **Validate:** `uv run hotel-report validate my_report.json` — fix any errors.
5. **Render:** `uv run hotel-report render my_report.json report.docx`.

## Rules

- **Always run through `uv`** — never `pip`/`python` directly (keeps the locked,
  cross-platform environment).
- Rates may be numbers (rendered `$1,250`) or strings (`"Waived"`).
- `distance_from_venue` is the number only (template adds " miles"); `cutoff` is
  the lead time only (template adds " prior to arrival").
- To change the report **layout**, edit `assets/source_template.docx` and rerun
  `uv run hotel-report build-template …`; to change **content**, edit the JSON.
- Getting the data is out of scope for now — just satisfy the schema.
