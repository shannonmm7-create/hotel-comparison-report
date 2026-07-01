"""Shared fixtures and helpers for the test suite."""

from __future__ import annotations

import json
import re
import zipfile
from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest
from docx import Document
from docx.oxml.ns import qn

EXAMPLE = files("hotel_report").joinpath("data/example_report.json")
SOURCE_TEMPLATE = "assets/source_template.docx"

# A minimal valid report (one hotel, no optional website_url / tripadvisor / bullets).
MINIMAL: dict[str, Any] = {
    "prepared_for": "Event",
    "arrival_date": "Jan 1, 2027",
    "departure_date": "Jan 2, 2027",
    "venue_name": "Venue",
    "hotels": [
        {
            "name": "Hotel",
            "address_line_1": "1 Main St",
            "city_state_zip": "Town, ST 00000",
            "rooms": [{"room_type": "King", "offered_rate": 100, "rack_rate": 200}],
            "distance_from_venue": "1.0",
            "cutoff": "30 days",
        }
    ],
}


@pytest.fixture
def example_data() -> dict[str, Any]:
    """The bundled example report data, parsed from JSON."""
    with EXAMPLE.open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def doc_text(path: str | Path) -> str:
    """All visible text of a .docx, paragraphs and tables, in document order."""
    doc = Document(str(path))
    return "\n".join("".join((t.text or "") for t in p.iter(qn("w:t"))) for p in doc.element.body.iter(qn("w:p")))


def hyperlink_targets(path: str | Path) -> list[str]:
    """The external hyperlink relationship targets in a rendered .docx."""
    rels = zipfile.ZipFile(str(path)).read("word/_rels/document.xml.rels").decode()
    return re.findall(r'Target="(https?://[^"]+)"', rels)
