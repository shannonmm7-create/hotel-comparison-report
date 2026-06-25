# Hotel Comparison Report Skill

A Claude skill for generating **JC Room Blocks Hotel Comparison Reports** as Word
(`.docx`) documents with pixel-identical formatting every time. You provide the
hotel details; a deterministic Python script fills them into the approved layout
so fonts, spacing, tables, and dividers never drift between reports.

## Repository layout

- **`hotel-comparison-report/`** — the skill itself
  - `SKILL.md` — instructions and the JSON data schema
  - `scripts/build_report.py` — the generator; all formatting is hardcoded here,
    extracted from the approved Hepburn/Donaldson reference report. It also
    re-opens the saved file and audits the formatting (spacer sizes, table
    widths) before reporting success.
  - `assets/` — the JC Room Blocks and TripAdvisor logos, plus
    `example_report.json` showing the expected data shape
  - `evals/evals.json` — the test prompts used to validate the skill
- **`hotel-comparison-report-workspace/`** — test/evaluation results
  - `iteration-1/` — graded runs comparing the skill vs. a no-skill baseline
    (skill: 100% of formatting checks passed; baseline: 37.5%)
  - `grade_docx.py` — programmatic grader for the formatting contract
  - `generate_review_py39.py`, `viewer.html` — local eval-review viewer
    (patched for Python 3.9)

## Installing the skill

Copy the skill folder into your Claude skills directory:

```bash
cp -R hotel-comparison-report ~/.claude/skills/hotel-comparison-report
```

Then, in a new Claude session, just ask for a hotel comparison report and paste
in the hotel offers — the skill triggers automatically.

## Regenerating a report manually

```bash
pip3 install python-docx
python3 hotel-comparison-report/scripts/build_report.py data.json "Hotel Comparison Report.docx"
```

See `hotel-comparison-report/assets/example_report.json` for the data format.
