"""Render the Hotel Comparison Report ``.docx`` from validated data.

The whole engine is docxtpl (Jinja2 over Word XML). The only non-obvious parts —
currency formatting, per-hotel RichText hyperlinks, and why ``autoescape`` is
mandatory — are explained inline and in ``docs/docx-templating-notes.md``.
"""
from __future__ import annotations

import io
import re
from importlib.resources import files
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docxtpl import DocxTemplate, RichText
from jinja2 import Environment

DEFAULT_TEMPLATE = files("hotel_report").joinpath("templates/hotel_comparison_report.docx")

# Matches the approved hyperlink look captured from the source template.
_LINK_BLUE = "0000FF"
_NAME_SIZE = 24  # half-points -> 12pt
_TA_SIZE = 21    # half-points -> 10.5pt

# A whole Jinja token ({{ }}, {% %}, {# #}); used to detect unrendered residue.
_TOKEN_RE = re.compile(r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}", re.S)


class RenderError(RuntimeError):
    pass


def usd(value):
    """Format a rate as US currency. Numbers get a ``$`` and thousands
    separators (279 -> $279, 1250 -> $1,250). Strings pass through unchanged, so
    the caller controls edge cases ('Waived', '$305 + tax')."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return f"${value:,.0f}" if float(value).is_integer() else f"${value:,.2f}"
    return str(value)


def _jinja_env() -> Environment:
    # autoescape=True is REQUIRED: data may contain & < > which would otherwise
    # produce invalid document XML. docxtpl's RichText is autoescape-safe, so
    # the hyperlinks below still render as real links.
    env = Environment(autoescape=True)
    env.filters["usd"] = usd
    return env


def _build_context(tpl: DocxTemplate, data: dict) -> dict:
    ctx = {k: data[k] for k in ("prepared_for", "arrival_date", "departure_date", "venue_name")}
    hotels = []
    for hotel in data["hotels"]:
        hotel = dict(hotel)
        # hotel name -> RichText hyperlink (approved look: bold, underline, blue, 12pt)
        url = hotel.get("website_url")
        name = RichText()
        name.add(hotel["name"], url_id=tpl.build_url_id(url) if url else None,
                 bold=True, underline=bool(url), color=_LINK_BLUE if url else "000000", size=_NAME_SIZE)
        hotel["name_link"] = name
        # tripadvisor -> RichText hyperlink (underline, blue, 10.5pt, Arial)
        ta = hotel.get("tripadvisor") or {}
        ta_url = ta.get("url")
        ta_link = RichText()
        ta_link.add(ta.get("text", ""), url_id=tpl.build_url_id(ta_url) if ta_url else None,
                    underline=bool(ta_url), color=_LINK_BLUE if ta_url else "000000",
                    size=_TA_SIZE, font="Arial")
        hotel["tripadvisor_link"] = ta_link
        for key in ("features", "concessions", "contracting_options"):
            hotel.setdefault(key, [])
        hotels.append(hotel)
    ctx["hotels"] = hotels
    return ctx


def _part_elements(doc):
    """The body plus every header/footer element — docxtpl renders all of them,
    so residue detection must look at all of them too."""
    out, seen = [doc.element.body], {id(doc.element.body)}
    for sec in doc.sections:
        for hf in (sec.header, sec.first_page_header, sec.even_page_header,
                   sec.footer, sec.first_page_footer, sec.even_page_footer):
            el = getattr(hf, "_element", None)
            if el is None:
                el = hf.part.element
            if id(el) not in seen:
                seen.add(id(el))
                out.append(el)
    return out


def _jinja_tokens(doc) -> list[str]:
    """Every Jinja token in the document, coalescing runs per paragraph (Word
    can split a token across runs) across body, headers and footers."""
    toks = []
    for part in _part_elements(doc):
        for p in part.iter(qn("w:p")):
            line = "".join((t.text or "") for t in p.iter(qn("w:t")))
            toks.extend(_TOKEN_RE.findall(line))
    return toks


def find_residue(path) -> list[str]:
    """Jinja tokens surviving anywhere in a rendered document (body/headers/footers)."""
    return _jinja_tokens(Document(str(path)))


def render(data: dict, output_path, template=None) -> dict:
    """Fill the template from ``data`` and write ``output_path``.

    Returns a small summary; raises :class:`RenderError` if any *template* token
    fails to render. Data that merely contains ``{{`` / ``%}`` is not flagged —
    only tokens that were actually present in the template count as residue.
    (Missing data is caught earlier by the schema validator.)"""
    if template is None:
        raw = DEFAULT_TEMPLATE.read_bytes()  # bytes so it works from a zipped install too
        template_tokens = set(_jinja_tokens(Document(io.BytesIO(raw))))
        tpl = DocxTemplate(io.BytesIO(raw))
    else:
        template_tokens = set(_jinja_tokens(Document(str(template))))
        tpl = DocxTemplate(str(template))
    tpl.render(_build_context(tpl, data), jinja_env=_jinja_env())
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tpl.save(str(output_path))
    residue = sorted(set(find_residue(output_path)) & template_tokens)
    if residue:
        raise RenderError(f"unrendered template tokens remain: {residue}")
    return {
        "output": str(output_path),
        "hotels": len(data["hotels"]),
        "rooms": sum(len(h["rooms"]) for h in data["hotels"]),
    }
