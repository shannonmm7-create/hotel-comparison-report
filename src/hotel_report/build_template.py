"""
Deterministically transform the client's source ``.docx`` into a docxtpl
(Jinja2) template, preserving every bit of the approved visual formatting.

Why this file exists: the client ships a Word document whose *content* is
placeholder text (``[Hotel Name]``, ``$[Rate]`` …) laid out with exact fonts,
spacing, table styling and (approved) hyperlink look. We do **not** rebuild that
formatting by hand — we keep the document and only rewrite its text into Jinja
tags, then let :mod:`hotel_report.render` fill it. Re-run ``build-template``
whenever the client sends an updated source document.

The tricky OOXML/docxtpl details this relies on are documented in
``docs/docx-templating-notes.md`` — read that before editing this file.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from hotel_report._validate import validated

# lxml/python-docx OOXML elements have no useful static type here.
Element = Any


# --------------------------------------------------------------------------- #
# low-level run helpers                                                        #
# --------------------------------------------------------------------------- #
@validated
def _runs_with_text(el: Element) -> list[tuple[Element, Element]]:
    """(run, w:t) pairs for every run under ``el`` -- ``iter`` descends into
    ``<w:hyperlink>``, which ``Paragraph.runs`` does not (see notes)."""
    return [(r, r.find(qn("w:t"))) for r in el.iter(qn("w:r")) if r.find(qn("w:t")) is not None]


@validated
def _coalesce(runs: list[tuple[Element, Element]]) -> tuple[str, list[int]]:
    """Join every run's text into one string plus an owner map (char -> run index)."""
    text, owner = [], []
    for i, (_r, t) in enumerate(runs):
        s = t.text or ""
        text.append(s)
        owner.extend([i] * len(s))
    return "".join(text), owner


@validated
def _set_text(t: Element, s: str) -> None:
    """Set a ``<w:t>``'s text, preserving leading/trailing whitespace."""
    t.text = s
    t.set(qn("xml:space"), "preserve")


@validated
def _ptext(el: Element) -> str:
    """The coalesced visible text of ``el``."""
    return "".join((t.text or "") for _r, t in _runs_with_text(el))


@validated
def replace_tokens(el: Element, replacements: dict[str, str]) -> None:  # pylint: disable=too-many-locals
    """Replace literal substrings inside ``el`` while preserving run formatting.

    Works even when a placeholder is split across several runs (Word does this
    routinely): the coalesced text is scanned, then each replacement is spliced
    back into the run that owns its first character.
    """
    runs = _runs_with_text(el)
    if not runs:
        return
    text, owner = _coalesce(runs)
    spans = []
    for old, new in sorted(replacements.items(), key=lambda kv: -len(kv[0])):
        start = 0
        while (i := text.find(old, start)) >= 0:
            spans.append((i, i + len(old), new))
            start = i + len(old)
    if not spans:
        return
    spans.sort()
    buffers = ["" for _ in runs]
    i = si = 0
    n = len(text)
    while i < n:
        if si < len(spans) and i == spans[si][0]:
            s, e, new = spans[si]
            buffers[owner[s]] += new
            i, si = e, si + 1
        else:
            buffers[owner[i]] += text[i]
            i += 1
    for idx, (_r, t) in enumerate(runs):
        _set_text(t, buffers[idx])


@validated
def _make_tag_p(tag: str) -> Element:
    """A bare paragraph holding a Jinja control tag."""
    p = OxmlElement("w:p")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    _set_text(t, tag)
    r.append(t)
    p.append(r)
    return p


@validated
def _reset_to_placeholder(p: Element, tag: str) -> None:
    """Replace a paragraph's inline content with a single clean run holding
    ``tag``, keeping the paragraph properties and any image runs.

    Used for the hotel-name and TripAdvisor lines: in the source these are
    hyperlink *fields* (fldChar / instrText / bookmarks). A docxtpl RichText
    ``{{r ... }}`` inserted at render time supplies a fresh, correct hyperlink,
    so all that legacy field cruft must be stripped first — otherwise the
    RichText lands inside leftover field markup and won't render in Word.
    """
    for child in list(p):
        if child.tag == qn("w:pPr"):
            continue
        # keep an image/drawing run (e.g. an inline logo) if one is present
        if child.tag == qn("w:r") and (child.find(qn("w:drawing")) is not None or child.find(qn("w:pict")) is not None):
            continue
        p.remove(child)
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    _set_text(t, tag)
    r.append(t)
    p.append(r)


@validated
def _set_row_tag(tr: Element, tag: str) -> None:
    """Clear every cell of a table row and put a single Jinja tag in the first
    cell. docxtpl's ``{%tr%}`` handling replaces the whole row with that tag."""
    for i, tc in enumerate(tr.findall(qn("w:tc"))):
        for p in tc.findall(qn("w:p")):
            for r in p.findall(qn("w:r")):
                p.remove(r)
        if i == 0:
            p = tc.find(qn("w:p"))
            r = OxmlElement("w:r")
            t = OxmlElement("w:t")
            _set_text(t, tag)
            r.append(t)
            p.append(r)


@validated
def _find_p(body: Element, pred: Callable[[str], bool]) -> Element | None:
    """First paragraph whose coalesced text satisfies ``pred`` (or ``None``)."""
    for ch in body.iterchildren(qn("w:p")):
        if pred(_ptext(ch)):
            return ch
    return None


@validated
def _find_all_p(body: Element, pred: Callable[[str], bool]) -> list[Element]:
    """Every paragraph whose coalesced text satisfies ``pred``."""
    return [ch for ch in body.iterchildren(qn("w:p")) if pred(_ptext(ch))]


@validated
def _must_find(body: Element, pred: Callable[[str], bool]) -> Element:
    """Like :func:`_find_p` but raise if no paragraph matches (a required anchor)."""
    el = _find_p(body, pred)
    if el is None:
        raise RuntimeError("expected paragraph not found in source template")
    return el


@validated
def _bullet_loop(header_p: Element, item_var: str, iterable: str) -> None:
    """Turn the bullet paragraphs following a section header into a single
    ``{%p for %}`` loop, keeping the first bullet's '• + tab' formatting."""
    body = header_p.getparent()
    bullets = []
    sib = header_p.getnext()
    while sib is not None and sib.tag == qn("w:p") and _ptext(sib).lstrip().startswith("•"):
        bullets.append(sib)
        sib = sib.getnext()
    if not bullets:
        raise RuntimeError("no bullets after header: " + _ptext(header_p))
    tb = bullets[0]
    for extra in bullets[1:]:
        body.remove(extra)
    runs = _runs_with_text(tb)

    def _is_content(t: Element) -> bool:
        """True if the run holds the bullet's label text (not the • or the tab)."""
        s = t.text or ""
        return any(c.isalpha() for c in s) or "[" in s

    content_idx = next((i for i, (_r, t) in enumerate(runs) if _is_content(t)), len(runs) - 1)
    _set_text(runs[content_idx][1], "{{ " + item_var + " }}")
    for j in range(content_idx + 1, len(runs)):
        _set_text(runs[j][1], "")
    tb.addprevious(_make_tag_p("{%p for " + item_var + " in " + iterable + " %}"))
    tb.addnext(_make_tag_p("{%p endfor %}"))


# --------------------------------------------------------------------------- #
# the transform                                                               #
# --------------------------------------------------------------------------- #
@validated
def build(src_path: str | Path, out_path: str | Path) -> Path:  # noqa: PLR0915
    """Transform the source ``.docx`` at ``src_path`` into a Jinja template at
    ``out_path`` and return the output path."""
    # one linear OOXML transform — many locals/statements are expected here:
    # pylint: disable=too-many-locals,too-many-statements
    doc = Document(str(src_path))
    body = doc.element.body

    # event-level scalars (outside the hotel loop)
    replace_tokens(_must_find(body, lambda t: "Prepared for" in t), {"[Client/Event Name]": "{{ prepared_for }}"})
    replace_tokens(
        _must_find(body, lambda t: "[Arrival Date]" in t),
        {"[Arrival Date]": "{{ arrival_date }}", "[Departure Date]": "{{ departure_date }}"},
    )

    # anchors for hotel block 1 (the canonical loop body)
    p_name1 = _must_find(body, lambda t: t.strip() == "[Hotel Name]")
    p_addr1 = _find_all_p(body, lambda t: t.strip() == "[Hotel Address Line 1]")[0]
    p_city1 = _find_all_p(body, lambda t: t.strip() == "[City, State ZIP]")[0]
    p_ta1 = _find_all_p(body, lambda t: t.strip() == "[TripAdvisor rating/ranking with hyperlink]")[0]
    p_dist1 = _find_all_p(body, lambda t: t.startswith("Distance from"))[0]
    p_cut1 = _find_all_p(body, lambda t: t.startswith("Cut-off Date"))[0]
    feat_h = _find_all_p(body, lambda t: t.strip() == "Hotel Features:")[0]
    conc_h = _find_all_p(body, lambda t: t.strip() == "Concessions:")[0]
    ctr_h = _find_all_p(body, lambda t: t.strip() == "Contracting Option:")[0]
    p_name2 = _must_find(body, lambda t: t.strip() == "[Additional Hotel Name]")
    footer = _must_find(body, lambda t: "JC Room Blocks" in t)

    # hotel name + TripAdvisor are RichText hyperlinks -> use docxtpl's {{r ... }}
    # run syntax (plain {{ }} would nest the <w:hyperlink> inside a <w:t>, which
    # Word/LibreOffice will not render) and strip the source's hyperlink fields.
    _reset_to_placeholder(p_name1, "{{r hotel.name_link }}")
    _reset_to_placeholder(p_ta1, "{{r hotel.tripadvisor_link }}")
    # plain scalars
    replace_tokens(p_addr1, {"[Hotel Address Line 1]": "{{ hotel.address_line_1 }}"})
    replace_tokens(p_city1, {"[City, State ZIP]": "{{ hotel.city_state_zip }}"})
    # Consume the template's hardcoded " miles" / " prior to arrival" suffixes so
    # distance_from_venue and cutoff carry the full free-form display text
    # (e.g. "Across the street" / "30 days prior to arrival, by Mar 17").
    replace_tokens(
        p_dist1,
        {
            "[Venue Name]": "{{ venue_name }}",
            "[Driving distance from Google Maps] miles": "{{ hotel.distance_from_venue }}",
        },
    )
    replace_tokens(p_cut1, {"[# days/weeks/months] prior to arrival": "{{ hotel.cutoff }}"})
    # Correct the client template's misspelled footer email (Blcoks -> Blocks).
    replace_tokens(footer, {"JCRoomBlcoks": "JCRoomBlocks"})

    # rate table -> {%tr%} row loop (dedicated for/endfor rows around the data
    # row; docxtpl replaces each tag-row with a bare Jinja tag)
    tbl = body.findall(qn("w:tbl"))[0]
    rows = tbl.findall(qn("w:tr"))
    data_row = rows[1]
    for extra in rows[2:]:
        tbl.remove(extra)
    cells = data_row.findall(qn("w:tc"))
    replace_tokens(cells[0], {"[Room Type 1]": "{{ r.room_type }}"})
    replace_tokens(cells[1], {"$[Rate]": "{{ r.offered_rate | usd }}"})
    replace_tokens(cells[2], {"$[Rack Rate]": "{{ r.rack_rate | usd }}"})
    for_row = copy.deepcopy(data_row)
    end_row = copy.deepcopy(data_row)
    _set_row_tag(for_row, "{%tr for r in hotel.rooms %}")
    _set_row_tag(end_row, "{%tr endfor %}")
    data_row.addprevious(for_row)
    data_row.addnext(end_row)

    # bullet sections -> {%p for %} loops
    _bullet_loop(feat_h, "f", "hotel.features")
    _bullet_loop(conc_h, "c", "hotel.concessions")
    _bullet_loop(ctr_h, "co", "hotel.contracting_options")

    # wrap hotel block 1 in {%p for hotel in hotels %} ... {%p endfor %}
    p_name1.addprevious(_make_tag_p("{%p for hotel in hotels %}"))
    p_name2.addprevious(_make_tag_p("{%p endfor %}"))

    # delete the 2nd hardcoded hotel block (name2 .. up to the footer)
    to_delete = []
    sib = p_name2
    while sib is not None and sib is not footer:
        to_delete.append(sib)
        sib = sib.getnext()
    for el in to_delete:
        body.remove(el)

    _drop_orphan_hyperlink_rels(doc, body)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return Path(out_path)


@validated
def _drop_orphan_hyperlink_rels(doc: Element, body: Element) -> None:
    """Remove hyperlink relationships no longer referenced by any ``<w:hyperlink>``
    (e.g. the deleted hotel's stale reference URLs), so no wrong links linger."""
    used = {h.get(qn("r:id")) for h in body.iter(qn("w:hyperlink")) if h.get(qn("r:id"))}
    rels = doc.part.rels
    for rid, rel in list(rels.items()):
        if rel.reltype.endswith("/hyperlink") and rid not in used:
            rels.pop(rid)
