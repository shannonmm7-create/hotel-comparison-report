---
name: hotel-comparison-report
description: Generate the JC Room Blocks Hotel Comparison Report (.docx) from JSON data by filling the approved Word template with docxtpl. Use when asked to build, render, or produce a hotel comparison report, room-block report, or fill the JC hotel template. Assemble and validate JSON, then run the plugin's uv-based CLI; never hand-build the .docx.
---

# Hotel Comparison Report

Render the JC Room Blocks Hotel Comparison Report `.docx` by filling the approved
Word template. Produce a JSON data file and run the bundled CLI; the tool owns
all formatting. Never build or hand-edit the `.docx`.

The plugin root is two directories above this `SKILL.md`. Resolve that absolute
path first and use it as `<plugin-root>` below. The plugin may be installed in a
Codex cache, so do not assume the current working directory is the plugin root.

Full guide: [`AGENTS.md`](../../AGENTS.md). Engine internals and Word-template
gotchas: [`docs/docx-templating-notes.md`](../../docs/docx-templating-notes.md).

## Workflow

1. Choose absolute paths in the user's writable workspace for the input JSON and
   output `.docx`. Do not put user deliverables inside the installed plugin.
2. Sync once: `uv --directory <plugin-root> sync`.
3. Inspect the contract: `uv --directory <plugin-root> run hotel-report schema`.
4. If useful, create a starter file:
   `uv --directory <plugin-root> run hotel-report example <input-json>`.
5. Write or update the JSON to match
   `<plugin-root>/src/hotel_report/models.py`; do not add extra fields.
6. Validate:
   `uv --directory <plugin-root> run hotel-report validate <input-json>`.
7. Render:
   `uv --directory <plugin-root> run hotel-report render <input-json> <output-docx>`.

## Data shape

Top-level fields are `prepared_for`, `arrival_date`, `departure_date`,
`venue_name`, and `hotels[]`. Each hotel contains `name` (plus optional
`website_url`), `address_line_1`, `city_state_zip`, optional
`tripadvisor{text,url}`, `rooms[]{room_type,offered_rate,rack_rate}`, free-form
`features[]`, `concessions[]`, and `contracting_options[]` bullet lists, plus
`distance_from_venue` and `cutoff`.

## Rules

- Always run through `uv`; never use `pip` or invoke Python directly for the CLI.
- Rates may be numbers (rendered as currency) or strings such as `"Waived"`.
- Follow the live schema emitted by the bundled CLI when examples and prose differ.
- To change report layout, edit `<plugin-root>/assets/source_template.docx` and
  regenerate the packaged template. To change report content, edit the JSON.
- Data acquisition is outside this skill's scope unless the user supplies or
  explicitly requests a data source.
