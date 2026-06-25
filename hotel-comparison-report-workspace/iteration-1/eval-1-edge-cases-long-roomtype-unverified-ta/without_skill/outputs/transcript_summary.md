# Transcript Summary

## Task
Create a hotel comparison report (.docx) for the Birch/Kowalski wedding, May 14–16, 2027, venue Biltmore Estate, Asheville, NC, comparing the Grand Bohemian Hotel Asheville and The Radical.

## What was done
1. Created the output directory.
2. Attempted to use the docx skill's recommended toolchain (`npm install -g docx` for docx-js), but Node/npm was not available in the environment. Fell back to `python-docx`, which was already installed (system Python 3.9.6).
3. Wrote `build_report.py` (kept in this directory) using python-docx to generate the report with:
   - Title block: report title, couple names, dates, venue, prepared date, accent rule.
   - Overview paragraph.
   - A 3-column side-by-side comparison table (10 attribute rows): address, website (hyperlinked), TripAdvisor ranking (hyperlinked for the Grand Bohemian; noted as unavailable for The Radical since it is a newer hotel with no ranking), group rates (including the full long room-type name "Premier Two Queen Mountain View Suite with Balcony and Kitchenette"), dining/amenities, parking, concessions, contract type, distance to venue, and reservation cutoff dates. Styled with plum header row, shaded label column, alternating row tint, and live hyperlinks.
   - Per-hotel detail pages (one per page) covering ranking/reputation, group rates, features and amenities, concessions, contract terms, and logistics/deadlines.
   - A "Key Considerations" section highlighting the major differences: financial risk (courtesy block with no client responsibility vs. 90% attrition with 10-room/night minimum), rate gap, distance (0.2 vs 1.8 miles), booking cutoff (April 14, 2027 vs March 15, 2027), and reputation data availability.
   - A recommendation favoring the Grand Bohemian as the lower-risk option, while noting The Radical's lower rates.
4. Ran the script to produce `Birch-Kowalski_Wedding_Hotel_Comparison_Report.docx`.
5. Validation: the skill's `validate.py` could not run (requires Python 3.10+, only 3.9.6 available). Instead verified the file is a sound ZIP archive (`zipfile.testzip`), re-opened it with python-docx, and confirmed structure (57 paragraphs, 1 table of 11 rows x 3 columns) and table contents.

## Output files
- `Birch-Kowalski_Wedding_Hotel_Comparison_Report.docx` — the final report.
- `build_report.py` — the generation script (for reproducibility).
- `transcript_summary.md` — this file.

## Notes / data handling
- All facts (rates, concessions, contract terms, distances, cutoff dates, links) were taken verbatim from the user's brief; no external research was performed.
- The Radical's missing TripAdvisor ranking is explicitly noted in the report rather than omitted or fabricated.
- Parking rates are flagged "subject to change" as specified.
