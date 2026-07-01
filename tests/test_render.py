import copy
import re
import zipfile

import pytest

from conftest import doc_text, hyperlink_targets
from hotel_report.render import find_residue, render, usd


@pytest.fixture
def rendered(example_data, tmp_path):
    out = tmp_path / "report.docx"
    summary = render(example_data, out)
    return out, summary


def test_summary_counts(rendered):
    _out, summary = rendered
    assert summary["hotels"] == 3
    assert summary["rooms"] == 6  # 3 + 2 + 1


def test_no_template_tokens_survive(rendered):
    out, _ = rendered
    assert find_residue(out) == []


def test_all_hotels_present(rendered):
    out, _ = rendered
    text = doc_text(out)
    for name in ("The Dewberry", "Hotel Bennett", "The Restoration"):
        assert name in text


def test_distinct_per_room_rates(rendered):
    """The bug that broke the naive design: 3 room types in one hotel must show
    3 different rates, formatted with thousands separators."""
    out, _ = rendered
    text = doc_text(out)
    for rate in ("$279", "$309", "$1,250", "$389", "$419", "$345"):
        assert rate in text, rate


def test_special_characters_escaped(rendered):
    out, _ = rendered
    assert "restaurant & bar" in doc_text(out)


def test_per_hotel_hyperlinks_and_no_stale_targets(rendered):
    out, _ = rendered
    targets = hyperlink_targets(out)
    assert "https://www.thedewberrycharleston.com/" in targets
    assert "https://www.hotelbennett.com/" in targets
    assert "https://www.therestorationhotel.com/" in targets
    # the source template's stale reference links must never leak through
    joined = " ".join(targets)
    assert "hyatt" not in joined.lower()
    assert "d7321091" not in joined  # Hyatt House Charleston TripAdvisor id


def test_shared_venue_name(rendered):
    out, _ = rendered
    assert doc_text(out).count("Legare Waring House") == 3


def test_variable_length_bullets(rendered):
    """Hotels have different numbers of feature bullets; all must appear."""
    out, _ = rendered
    text = doc_text(out)
    assert "Rooftop pool bar – Fiat Lux" in text          # Bennett only
    assert "Complimentary bike rentals" in text            # Restoration only


def test_usd_filter_units():
    assert usd(279) == "$279"
    assert usd(1250) == "$1,250"
    assert usd(1250.5) == "$1,250.50"
    assert usd("Waived") == "Waived"
    assert usd("$305") == "$305"


def test_hyperlinks_valid_not_nested_in_text(rendered):
    """Regression: RichText hyperlinks must be real <w:hyperlink> siblings, never
    nested inside a <w:t> (which renders invisibly in Word/LibreOffice — the bug
    that made hotel names disappear)."""
    out, _ = rendered
    xml = zipfile.ZipFile(str(out)).read("word/document.xml").decode()
    assert re.search(r"<w:t[^>]*>[^<]*<w:hyperlink", xml) is None
    # the hotel name text lives *inside* a hyperlink element
    assert re.search(r"<w:hyperlink\b(?:(?!</w:hyperlink>).)*The Dewberry", xml, re.S)


def test_data_containing_jinja_delimiters_is_not_residue(example_data, tmp_path):
    """A data value that happens to contain '{{' or '%}' is content, not an
    unrendered template token, and must not fail the render."""
    data = copy.deepcopy(example_data)
    data["hotels"][0]["features"].append("See note {{VIP}} — deposit 50%} of block")
    out = tmp_path / "ok.docx"
    summary = render(data, out)  # must not raise RenderError
    assert summary["hotels"] == 3
    assert "See note {{VIP}}" in doc_text(out)
