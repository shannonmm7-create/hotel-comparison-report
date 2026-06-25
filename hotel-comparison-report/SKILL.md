---
name: hotel-comparison-report
description: Generate a JC Room Blocks Hotel Comparison Report as a Word (.docx) document with pixel-identical formatting every time. Use this skill whenever the user wants to create, build, or update a hotel comparison report, hotel room block report, or hotel offer summary for a wedding, conference, or group event — including when they provide hotel offers, group rates, concessions, or TripAdvisor info and want them compiled into a client-ready report. Always use this skill instead of building the Word document by hand; it guarantees the exact approved layout and spacing.
---

# Hotel Comparison Report Generator

This skill produces JC Room Blocks "Hotel Comparison Report" Word documents.
The entire layout (fonts, 6 pt / 10 pt spacers, gray-shaded rate tables,
divider lines, logos) is hardcoded in `scripts/build_report.py`, which was
built from the approved Hepburn/Donaldson reference report. Your only job is
to assemble accurate JSON data — never construct or edit the .docx directly,
and never modify the formatting constants in the script. That is what makes
every report come out identical.

## Workflow

1. **Gather the data.** From the user's notes, emails, or prior conversation,
   collect for the report: client/event name, event dates, venue name, and for
   each hotel: name, website URL, address, TripAdvisor ranking + URL, room
   rates, features, concessions, contracting options, distance from venue, and
   cut-off date.
2. **Write the JSON file** (schema below). Model it on
   `assets/example_report.json` — read that file before writing your first
   report.
3. **Run the generator:**
   ```bash
   python3 <skill_dir>/scripts/build_report.py data.json "Hotel Comparison Report - <Client>.docx"
   ```
   (Requires `python-docx`; install with `pip3 install python-docx` if missing.)
4. **Check the output.** The script audits the saved file (spacer sizes, table
   widths, paragraph spacing) and prints the result. If the audit fails, fix
   the data — do not hand-edit the document. Relay any `NEEDS VERIFICATION`
   lines to the user under a "Needs Verification" heading in your response.

## JSON schema

Top level:

| field | notes |
|---|---|
| `prepared_for` | e.g. `"Hepburn/Donaldson Wedding"` — rendered as "Prepared for …" |
| `event_dates` | e.g. `"April 16, 2027 – April 18, 2027"` (use an en dash) |
| `venue_name` | e.g. `"Carolina Yacht Club"` — used in "Distance from {venue}: …" |
| `hotels` | array of hotel objects, in the order they should appear |
| `contact_line` | optional; defaults to the standard JC Room Blocks contact line |

Each hotel:

| field | notes |
|---|---|
| `name` | hotel name; hyperlinked when `website_url` is present |
| `website_url` | optional but strongly preferred |
| `address` | street line only |
| `city_state_zip` | e.g. `"Charleston, SC 29401"` |
| `tripadvisor` | `{"ranking": "#X of Y Hotels in City", "url": "..."}` — see below |
| `rates` | array of `{"room_type", "offered_rate", "rack_rate"}`; rates as `"$279"` |
| `rate_notes` | optional; defaults to the standard two `*Rates…` notes |
| `features` | array of strings (no bullet characters — the script adds them) |
| `concessions` | array of strings |
| `contracting_options` | array of strings; prefix an item with `"> "` to make it an indented sub-bullet |
| `distance_from_venue` | e.g. `"2.2 miles"` |
| `cutoff_date` | text after the fixed "Cut-off Date: (last date…):" prefix, e.g. `"30 days prior to arrival, by March 17, 2027"` |

## Data accuracy rules

- **TripAdvisor**: the ranking must be in exactly the form
  `#X of Y Hotels in [City]` with `url` pointing to that hotel's TripAdvisor
  page. No bubble ratings. If you cannot verify the ranking (e.g. you have no
  web access, the hotel is unopened, or the user didn't provide it), set
  `"ranking": null` and optionally a short `"note"` (e.g. `"hotel opens
  8/1/2026"`); the report will print "TripAdvisor rating not verified" and the
  script will list it under NEEDS VERIFICATION for you to surface to the user.
- Use the user's wording for features/concessions/options verbatim where
  given; don't invent amenities or rates. Anything you had to assume or could
  not confirm belongs in your "Needs Verification" summary to the user.
- Keep room type names concise so they fit on one line; the script sizes the
  Room Type column automatically and will wrap rather than overflow the page.
- The dates line and any date ranges use an en dash (–), not a hyphen.

## What the script guarantees (so you don't have to)

Title block with JC Room Blocks logo; per-hotel layout with TripAdvisor logo;
single 6 pt spacers after the city line, Features, Concessions, and
Contracting Option sections; single 10 pt spacers around each divider line;
centered gray-shaded rate tables that always fit the page; 1.15 body line
spacing with zero space before/after; and exactly one JC Room Blocks contact
line at the very end. If the user asks for a different layout, tell them the
layout is fixed by design and changes should be made once in
`scripts/build_report.py` so all future reports stay consistent.
