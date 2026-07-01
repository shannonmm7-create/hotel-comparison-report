import re
import zipfile

from conftest import SOURCE_TEMPLATE
from hotel_report.build_template import build


def _document_xml(path) -> str:
    return zipfile.ZipFile(str(path)).read("word/document.xml").decode()


def test_build_produces_jinja_loops(tmp_path):
    out = tmp_path / "tpl.docx"
    build(SOURCE_TEMPLATE, out)
    xml = _document_xml(out)
    assert "{%p for hotel in hotels %}" in xml
    assert "{%tr for r in hotel.rooms %}" in xml
    for iterable in ("hotel.features", "hotel.concessions", "hotel.contracting_options"):
        assert f" in {iterable} %}}" in xml  # each bullet section became a {%p for ... %} loop


def test_build_leaves_no_source_placeholders(tmp_path):
    out = tmp_path / "tpl.docx"
    build(SOURCE_TEMPLATE, out)
    xml = _document_xml(out)
    # every bracketed source placeholder must have been converted
    leftovers = re.findall(r"\[[^\]]+\]|\$\[", xml)
    assert leftovers == [], leftovers


def test_build_strips_orphaned_hyperlink_rels(tmp_path):
    out = tmp_path / "tpl.docx"
    build(SOURCE_TEMPLATE, out)
    rels = zipfile.ZipFile(str(out)).read("word/_rels/document.xml.rels").decode()
    assert "hyatt" not in rels.lower()
    assert "tripadvisor" not in rels.lower()
