# Transcript Summary

## Task
Generate a JC Room Blocks Hotel Comparison Report (.docx) for the Birch/Kowalski Wedding, May 14–16, 2027, venue: Biltmore Estate, Asheville, comparing the Grand Bohemian Hotel Asheville and The Radical.

## What I did
1. Read `hotel-comparison-report/SKILL.md` and the `assets/example_report.json` schema example.
2. Assembled the report data into `birch_kowalski_report.json`, following the schema:
   - Used the user's wording for rates, features, concessions, contracting options, distances, and cut-off dates.
   - Event dates formatted with an en dash: "May 14, 2027 – May 16, 2027".
   - Grand Bohemian: TripAdvisor ranking `#18 of 28 Hotels in Asheville` with the provided URL.
   - The Radical: user could not find a TripAdvisor ranking (newer hotel), so per the skill rules I set `"ranking": null` with note "newer hotel; ranking not available" and used the Asheville hotels TripAdvisor index page as the URL. The report prints "TripAdvisor rating not verified".
   - Kept the long room type name verbatim ("Premier Two Queen Mountain View Suite with Balcony and Kitchenette"); the script wraps it within the page.
3. Ran `scripts/build_report.py` — did not hand-edit the docx or modify the script.
4. Audit passed: 10 six-pt spacers, 4 ten-pt spacers, 2 rate tables, all within page width.

## Outputs
- `Hotel Comparison Report - Birch_Kowalski.docx`
- `birch_kowalski_report.json`

## Needs Verification
- **The Radical: TripAdvisor ranking** — no ranking was available (newer hotel). The report shows "TripAdvisor rating not verified". If a ranking appears later, update the JSON and regenerate.

## Minor assumptions (flagging for transparency)
- Parking lines normalized to the report's standard phrasing: "Valet parking $35 per car, per night (subject to change)" and "Self-parking $25 per car, per night (subject to change)".
- "95 Roberts St" expanded to "95 Roberts Street" for address consistency.
- Cut-off dates phrased as "30 days prior to arrival, by April 14, 2027" and "60 days prior to arrival, by March 15, 2027" to match the standard format.
