"""Tests for building the Jinja template from the source .docx."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from conftest import SOURCE_TEMPLATE
from hotel_report.build_template import build


def _document_xml(path: str | Path) -> str:
    """The raw word/document.xml of a .docx."""
    return zipfile.ZipFile(str(path)).read("word/document.xml").decode()


def test_build_produces_jinja_loops(tmp_path: Path) -> None:
    """The generated template contains the hotel, room-row and bullet loops."""
    out = tmp_path / "tpl.docx"
    build(SOURCE_TEMPLATE, out)
    xml = _document_xml(out)
    assert "{%p for hotel in hotels %}" in xml
    assert "{%tr for r in hotel.rooms %}" in xml
    for iterable in ("hotel.features", "hotel.concessions", "hotel.contracting_options"):
        assert f" in {iterable} %}}" in xml  # each bullet section became a {%p for ... %} loop


def test_build_leaves_no_source_placeholders(tmp_path: Path) -> None:
    """Every bracketed source placeholder is converted to a Jinja tag."""
    out = tmp_path / "tpl.docx"
    build(SOURCE_TEMPLATE, out)
    xml = _document_xml(out)
    leftovers = re.findall(r"\[[^\]]+\]|\$\[", xml)
    assert leftovers == [], leftovers


def test_build_strips_orphaned_hyperlink_rels(tmp_path: Path) -> None:
    """The deleted hotel's stale hyperlink relationships are removed."""
    out = tmp_path / "tpl.docx"
    build(SOURCE_TEMPLATE, out)
    rels = zipfile.ZipFile(str(out)).read("word/_rels/document.xml.rels").decode()
    assert "hyatt" not in rels.lower()
    assert "tripadvisor" not in rels.lower()
