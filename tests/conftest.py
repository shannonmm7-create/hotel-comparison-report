import json
import re
import zipfile
from importlib.resources import files

import pytest
from docx import Document
from docx.oxml.ns import qn

EXAMPLE = files("hotel_report").joinpath("data/example_report.json")
SOURCE_TEMPLATE = "assets/source_template.docx"


@pytest.fixture
def example_data():
    with EXAMPLE.open(encoding="utf-8") as fh:
        return json.load(fh)


def doc_text(path) -> str:
    """All visible text of a .docx, paragraphs and tables, in document order."""
    doc = Document(str(path))
    return "\n".join(
        "".join((t.text or "") for t in p.iter(qn("w:t")))
        for p in doc.element.body.iter(qn("w:p"))
    )


def hyperlink_targets(path) -> list[str]:
    rels = zipfile.ZipFile(str(path)).read("word/_rels/document.xml.rels").decode()
    return re.findall(r'Target="(https?://[^"]+)"', rels)
