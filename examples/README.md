# Example output

**[`example_report.docx`](example_report.docx)** is a rendered Hotel Comparison
Report — open it to see exactly what this tool produces. (In VS Code, the
recommended *Office Viewer* extension previews it inline; otherwise open it in
Word / Google Docs / LibreOffice.)

It was generated from the bundled example data:

```bash
uv run hotel-report example example_data.json          # the input JSON
uv run hotel-report render  example_data.json examples/example_report.docx
```

What to look for (things a naive find-and-replace gets wrong):

- **3 hotels** rendered from a template that hard-coded 2 — the hotel block loops.
- **Distinct rate per room**, incl. the 3 different rooms of *The Dewberry*
  (`$279 / $309 / $1,250`) — with thousands separators.
- **Variable-length bullet lists** (each hotel has a different set of features /
  concessions / contracting options).
- **Per-hotel hyperlinks** on the hotel name and TripAdvisor line (no stale links
  from the source template).
- Approved formatting preserved: fonts, spacing, the gray rate tables, bullets.
