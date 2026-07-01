# Hotel Comparison Report

Deterministically render the **JC Room Blocks Hotel Comparison Report** (`.docx`)
from a small JSON data file — with the client's approved formatting preserved
exactly (fonts, spacing, gray rate tables, bullet lists, and per-hotel
hyperlinks).

The report is produced by **filling an approved Word template**, not by rebuilding
the document in code. The engine is [docxtpl](https://docxtpl.readthedocs.io/)
(Jinja2 over Word XML). The template ships in the package and is regenerable from
the client's source `.docx`.

> 👀 **See a rendered result:** [`examples/example_report.docx`](examples/example_report.docx)
> (open in Word, or preview inline with the recommended VS Code *Office Viewer*
> extension).

```
data (JSON)  ──validate──▶  hotel-report render  ──▶  report .docx
   ▲                              │
   └── conforms to the JSON Schema (`uv run hotel-report schema`) — the only data-source seam
```

## Why this exists / design in one paragraph

The template repeats content at three levels — **hotels**, **rate-table rows**,
and **bullet lists** — and its two example hotels are not even structurally
identical. A flat find-and-replace therefore *cannot* fill it correctly (it would
give every room the same rate and leave hyperlinks pointing at the wrong hotel).
So we convert the template to Jinja loops and fill it with a validated, nested
data structure. The OOXML/docxtpl gotchas we hit (and solved) are written up in
[`docs/docx-templating-notes.md`](docs/docx-templating-notes.md) — read that
before touching `build_template.py` or `render.py`.

## Quick start (uv)

Everything runs through [uv](https://docs.astral.sh/uv/) so the environment is
locked and identical on macOS, Windows, and Linux. Install uv once
(`curl -LsSf https://astral.sh/uv/install.sh | sh`, or `winget install astral-sh.uv`),
then run these from the repo **in order** — step 2 creates the `my_report.json`
that steps 3–4 read:

```bash
uv sync                                                   # 1. install locked deps (uv fetches Python 3.14)
uv run hotel-report example my_report.json                # 2. write a starter my_report.json — then edit it
uv run hotel-report validate my_report.json               # 3. check it against the schema
uv run hotel-report render my_report.json report.docx     # 4. fill the template -> report.docx
```

(`render` reads `my_report.json`; run step 2 first or point it at your own JSON
file, otherwise you'll get `error: no such file: my_report.json`.)

The project targets **Python 3.14** — uv installs it for you, no system Python
needed. The dev quality gate (ruff, black, mypy, pylint, interrogate, bandit,
codespell, pytest) runs via [`nox`](https://nox.thea.codes/): `uv run nox`.

Other commands:

```bash
uv run hotel-report schema           # print the JSON Schema (the data contract)
uv run hotel-report build-template assets/source_template.docx \
      src/hotel_report/templates/hotel_comparison_report.docx   # regenerate the template
uv run pytest                        # run the test suite
```

## The data contract

`hotel-report render` accepts one JSON object. The authoritative contract is the
Pydantic models in [`src/hotel_report/models.py`](src/hotel_report/models.py); run
`uv run hotel-report schema` for the JSON Schema generated from them, or
`uv run hotel-report example` for a complete example. Shape:

```jsonc
{
  "prepared_for": "Rivera-Okafor Wedding",
  "arrival_date": "May 14, 2027",
  "departure_date": "May 16, 2027",
  "venue_name": "Legare Waring House",          // shared; distances are from here
  "hotels": [
    {
      "name": "The Dewberry",
      "website_url": "https://…",                // makes the name a hyperlink
      "address_line_1": "334 Meeting Street",
      "city_state_zip": "Charleston, SC 29403",
      "tripadvisor": { "text": "#4 of 45 hotels", "url": "https://…" },
      "rooms": [                                  // repeats one rate-table row each
        { "room_type": "King Room", "offered_rate": 279, "rack_rate": 459 }
      ],
      "features": ["On-site restaurant & bar – Henrietta's", "Fitness center"],
      "concessions": ["Complimentary Wi-Fi"],
      "contracting_options": ["Courtesy agreement — no financial responsibility"],
      "distance_from_venue": "8.1 miles",        // free-form; shown verbatim
      "cutoff": "30 days prior to arrival"        // free-form; shown verbatim
    }
  ]
}
```

Rates may be numbers (formatted as `$1,250`) or strings (`"Waived"`, passed
through as-is). `features` / `concessions` / `contracting_options` are free lists
— one bullet per string, any length.

> **Note:** wiring up *where the data comes from* is deliberately out of scope
> for now. This repo proves the templating is correct and deterministic; the JSON
> above is the fixed contract a future data pipeline must satisfy.

## Layout

```
src/hotel_report/
  models.py           Pydantic data contract (the schema is generated from it)
  cli.py              validate / render / schema / example / build-template
  render.py           docxtpl fill + currency + RichText hyperlinks
  build_template.py   source .docx -> Jinja template (regenerable)
  schema.py           validation + JSON-Schema export (Pydantic-backed)
  _validate.py        the @validated decorator (runtime signature enforcement)
  templates/          the generated Jinja template (shipped)
  data/               example_report.json (shipped; `hotel-report example`)
assets/source_template.docx   the client's source document (build input)
tests/                        schema + render + build-template tests
docs/docx-templating-notes.md the OOXML/docxtpl gotchas, written down
```

## For AI coding agents

This tool is meant to be driven by Claude, GitHub Copilot, or OpenAI Codex
interchangeably. The agent-facing instructions live in
[`AGENTS.md`](AGENTS.md); `.github/copilot-instructions.md` and the Claude skill
in `.claude/skills/` both delegate to it. All three tell the agent to do the same
thing: build a JSON file that matches the schema, then run
`uv run hotel-report render …`.
