"""Tests for rendering a report .docx from data."""

from __future__ import annotations

import copy
import re
import zipfile
from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest

from conftest import MINIMAL, doc_text, hyperlink_targets
from hotel_report.render import RenderSummary, find_residue, render, usd

Rendered = tuple[Path, RenderSummary]


@pytest.fixture
def rendered(example_data: dict[str, Any], tmp_path: Path) -> Rendered:
    """Render the example data and return (output path, summary)."""
    out = tmp_path / "report.docx"
    summary = render(example_data, out)
    return out, summary


def test_summary_counts(rendered: Rendered) -> None:
    """The summary reports the right hotel and room-row counts."""
    _out, summary = rendered
    assert summary["hotels"] == 3  # noqa: PLR2004
    assert summary["rooms"] == 6  # noqa: PLR2004  (3 + 2 + 1)


def test_no_template_tokens_survive(rendered: Rendered) -> None:
    """A successful render leaves no Jinja tokens behind."""
    out, _ = rendered
    assert find_residue(out) == []


def test_all_hotels_present(rendered: Rendered) -> None:
    """Every hotel name appears in the output."""
    out, _ = rendered
    text = doc_text(out)
    for name in ("The Dewberry", "Hotel Bennett", "The Restoration"):
        assert name in text


def test_distinct_per_room_rates(rendered: Rendered) -> None:
    """The bug that broke the naive design: 3 room types in one hotel must show
    3 different rates, formatted with thousands separators."""
    out, _ = rendered
    text = doc_text(out)
    for rate in ("$279", "$309", "$1,250", "$389", "$419", "$345"):
        assert rate in text, rate


def test_special_characters_escaped(rendered: Rendered) -> None:
    """An ampersand in data survives (autoescape produces valid XML)."""
    out, _ = rendered
    assert "restaurant & bar" in doc_text(out)


def test_per_hotel_hyperlinks_and_no_stale_targets(rendered: Rendered) -> None:
    """Each hotel's own links are present and the template's stale links are gone."""
    out, _ = rendered
    targets = hyperlink_targets(out)
    assert "https://www.thedewberrycharleston.com/" in targets
    assert "https://www.hotelbennett.com/" in targets
    assert "https://www.therestorationhotel.com/" in targets
    # the source template's stale reference links must never leak through
    joined = " ".join(targets)
    assert "hyatt" not in joined.lower()
    assert "d7321091" not in joined  # Hyatt House Charleston TripAdvisor id


def test_shared_venue_name(rendered: Rendered) -> None:
    """The shared venue name appears once per hotel block."""
    out, _ = rendered
    assert doc_text(out).count("Legare Waring House") == 3  # noqa: PLR2004


def test_variable_length_bullets(rendered: Rendered) -> None:
    """Hotels have different numbers of feature bullets; all must appear."""
    out, _ = rendered
    text = doc_text(out)
    assert "Rooftop pool bar – Fiat Lux" in text  # Bennett only
    assert "Complimentary bike rentals" in text  # Restoration only


def test_usd_filter_units() -> None:
    """The usd filter formats numbers and passes strings through."""
    assert usd(279) == "$279"
    assert usd(1250) == "$1,250"
    assert usd(1250.5) == "$1,250.50"
    assert usd("Waived") == "Waived"
    assert usd("$305") == "$305"


def test_usd_rounds_half_up() -> None:
    """Binary-float amounts round correctly (2.675 -> $2.68, not $2.67)."""
    assert usd(2.675) == "$2.68"
    assert usd(1234.005) == "$1,234.01"


def test_footer_email_is_corrected(rendered: Rendered) -> None:
    """The client template's misspelled footer email is fixed (Blcoks -> Blocks)."""
    text = doc_text(rendered[0])
    assert "Info@JCRoomBlocks.com" in text
    assert "Blcoks" not in text


def test_distance_and_cutoff_are_free_form(rendered: Rendered) -> None:
    """distance/cutoff carry the full display text (no hardcoded ' miles' / suffix)."""
    text = doc_text(rendered[0])
    assert "8.1 miles" in text and "miles miles" not in text
    assert "by April 14, 2027" in text  # the full cut-off phrasing survives


def test_sub_bullet_marker_is_stripped(rendered: Rendered) -> None:
    """A '> ' sub-item renders indented, without the literal '> ' marker."""
    text = doc_text(rendered[0])
    assert "Cut-off date for this option is 45 days" in text
    assert "> Cut-off date for this option" not in text


def test_tripadvisor_fallback_when_missing(tmp_path: Path) -> None:
    """A hotel without TripAdvisor data shows an explicit 'not verified' line."""
    out = tmp_path / "minimal.docx"
    render(MINIMAL, out)
    assert "TripAdvisor rating not verified" in doc_text(out)


def test_data_equal_to_template_token_is_not_residue(example_data: dict[str, Any], tmp_path: Path) -> None:
    """A feature whose text is exactly a template expression tag ({{ f }}) is data,
    not residue, and must render without error."""
    data = copy.deepcopy(example_data)
    data["hotels"][0]["features"].append("{{ f }}")
    out = tmp_path / "tok.docx"
    render(data, out)  # must not raise RenderError
    assert "{{ f }}" in doc_text(out)


def test_hyperlinks_valid_not_nested_in_text(rendered: Rendered) -> None:
    """Regression: RichText hyperlinks must be real <w:hyperlink> siblings, never
    nested inside a <w:t> (which renders invisibly in Word/LibreOffice — the bug
    that made hotel names disappear)."""
    out, _ = rendered
    xml = zipfile.ZipFile(str(out)).read("word/document.xml").decode()
    assert re.search(r"<w:t[^>]*>[^<]*<w:hyperlink", xml) is None
    # the hotel name text lives *inside* a hyperlink element
    assert re.search(r"<w:hyperlink\b(?:(?!</w:hyperlink>).)*The Dewberry", xml, re.S)


def test_render_hotel_without_optional_links(tmp_path: Path) -> None:
    """A hotel with no website_url and no tripadvisor renders (name as plain text,
    no dangling hyperlink relationships)."""
    out = tmp_path / "minimal.docx"
    summary = render(MINIMAL, out)
    assert summary["hotels"] == 1
    assert "Hotel" in doc_text(out)
    assert hyperlink_targets(out) == []


def test_render_accepts_explicit_template(example_data: dict[str, Any], tmp_path: Path) -> None:
    """render() accepts a --template-style explicit template path."""
    template = str(files("hotel_report").joinpath("templates/hotel_comparison_report.docx"))
    out = tmp_path / "explicit.docx"
    summary = render(example_data, out, template=template)
    assert summary["hotels"] == 3  # noqa: PLR2004
    assert find_residue(out) == []


def test_data_containing_jinja_delimiters_is_not_residue(example_data: dict[str, Any], tmp_path: Path) -> None:
    """A data value that happens to contain '{{' or '%}' is content, not an
    unrendered template token, and must not fail the render."""
    data = copy.deepcopy(example_data)
    data["hotels"][0]["features"].append("See note {{VIP}} — deposit 50%} of block")
    out = tmp_path / "ok.docx"
    summary = render(data, out)  # must not raise RenderError
    assert summary["hotels"] == 3  # noqa: PLR2004
    assert "See note {{VIP}}" in doc_text(out)
