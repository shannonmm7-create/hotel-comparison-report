# Transcript Summary — Martinez/Chen Wedding Hotel Comparison Report (without_skill)

## Task
Create a Word document comparing two hotel room block offers (The DeSoto Savannah and Hyatt Regency Savannah) for the Martinez/Chen wedding, October 9–11, 2026, near The Olde Pink House in Savannah, GA.

## What was done
1. Created the output directory and verified python-docx (v1.2.0) was available.
2. Built the .docx directly with a python-docx script (no docx skill invoked, per the "without_skill" condition). The script was run once and produced the final document with no errors.

## Document structure
- **Title block**: report title, wedding name, dates, ceremony venue, report date (June 11, 2026).
- **Overview**: brief framing of the two offers and comparison scope.
- **Side-by-Side Comparison table** (3 columns, 17 rows): address, website, TripAdvisor ranking, distance from venue, group rates vs. rack rates, savings, dining, pool, amenities, parking, Wi-Fi, gift bags, shoulder nights, block size, contract type, cut-off dates. Styled with a navy header row, shaded category column, and alternating row shading.
- **Rate Summary table**: all 5 room types with group rate, rack rate, and nightly savings, plus a tax/fee disclaimer note.
- **Key Considerations**: strengths and watch-outs bullet lists for each hotel. Notably flags the Hyatt's 80% attrition clause (client financial responsibility + credit card authorization) versus the DeSoto's zero-risk courtesy agreement.
- **Important Dates table**: Aug 25, 2026 (Hyatt cut-off), Sep 9, 2026 (DeSoto cut-off), Oct 9–11, 2026 (wedding weekend).
- **Summary Assessment**: frames the decision as price (Hyatt, ~$20–$40/night cheaper) vs. risk (DeSoto courtesy block, no attrition, better ranking, closer, shoulder-night rates, later cut-off), with recommended next steps.

## Output
- `Martinez-Chen_Wedding_Hotel_Comparison_Report.docx` (this directory)

## Notes
- All facts were taken directly from the offer details provided in the task; no web lookups were performed.
- Savings percentages (~40–42%) and walk-time estimates were derived arithmetically from the supplied rates and distances.
