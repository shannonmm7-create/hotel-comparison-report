"""Table-driven unit tests for internal helpers (drives branch coverage to 100%)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from hotel_report import build_template as bt
from hotel_report import cli
from hotel_report.render import RenderError, _control_tokens, _format_bullet
from hotel_report.render import render as render_fn


# --------------------------------------------------------------------------- #
# tiny OOXML builders                                                          #
# --------------------------------------------------------------------------- #
def _run(text: str) -> Any:
    """A ``<w:r>`` with a single ``<w:t>`` holding ``text``."""
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = text
    r.append(t)
    return r


def _para(*texts: str) -> Any:
    """A ``<w:p>`` with one run per text fragment."""
    p = OxmlElement("w:p")
    for txt in texts:
        p.append(_run(txt))
    return p


def _body(*paras: Any) -> Any:
    """A document body containing ``paras`` (keeps the owning doc alive via the tree)."""
    doc = Document()
    body = doc.element.body
    for p in paras:
        body.append(p)
    return body


# --------------------------------------------------------------------------- #
# build_template.replace_tokens                                               #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("runs", "replacements", "expected"),
    [
        pytest.param([], {"a": "b"}, "", id="no-runs-early-return"),
        pytest.param(["hello"], {"xyz": "Q"}, "hello", id="no-match-early-return"),
        pytest.param(["[Hotel Name]"], {"[Hotel Name]": "X"}, "X", id="single-run"),
        pytest.param(["[Hot", "el Name]"], {"[Hotel Name]": "X"}, "X", id="split-across-runs"),
        pytest.param(["[A] and [B]"], {"[A]": "1", "[B]": "2"}, "1 and 2", id="two-in-one-run"),
    ],
)
def test_replace_tokens(runs: list[str], replacements: dict[str, str], expected: str) -> None:
    """replace_tokens handles empty/no-match/single/split/multi-span cases."""
    p = _para(*runs)
    bt.replace_tokens(p, replacements)
    assert bt._ptext(p) == expected


# --------------------------------------------------------------------------- #
# build_template anchor finders                                               #
# --------------------------------------------------------------------------- #
def test_find_p_match_and_miss() -> None:
    """_find_p returns the matching paragraph, or None when nothing matches."""
    body = _body(_para("alpha"), _para("beta"))
    assert bt._ptext(bt._find_p(body, lambda t: "beta" in t)) == "beta"
    assert bt._find_p(body, lambda t: "zzz" in t) is None


def test_must_find_raises_when_missing() -> None:
    """_must_find raises for a required anchor that isn't present."""
    body = _body(_para("alpha"))
    with pytest.raises(RuntimeError, match="not found"):
        bt._must_find(body, lambda t: "zzz" in t)


# --------------------------------------------------------------------------- #
# build_template._bullet_loop                                                 #
# --------------------------------------------------------------------------- #
def test_bullet_loop_raises_without_bullets() -> None:
    """A section header with no following bullet is a malformed template."""
    header = _para("Hotel Features:")
    _body(header)
    with pytest.raises(RuntimeError, match="no bullets"):
        bt._bullet_loop(header, "f", "hotel.features")


def test_bullet_loop_blanks_trailing_runs() -> None:
    """The content run becomes the loop var and any trailing runs are blanked."""
    header = _para("Hotel Features:")
    bullet = _para("•", "content", "extra")  # •, content, trailing
    _body(header, bullet)
    bt._bullet_loop(header, "f", "hotel.features")
    assert bt._ptext(bullet) == "•{{ f }}"  # '•' kept, content->tag, 'extra' blanked


# --------------------------------------------------------------------------- #
# build_template._reset_to_placeholder                                        #
# --------------------------------------------------------------------------- #
def test_reset_to_placeholder_keeps_image_run() -> None:
    """An inline image/drawing run survives the reset; text/field runs do not."""
    p = OxmlElement("w:p")
    img_run = OxmlElement("w:r")
    img_run.append(OxmlElement("w:drawing"))
    p.append(img_run)
    p.append(_run("[Hotel Name]"))
    bt._reset_to_placeholder(p, "{{r hotel.name_link }}")
    assert p.find(qn("w:r")).find(qn("w:drawing")) is not None  # image kept
    assert bt._ptext(p) == "{{r hotel.name_link }}"  # placeholder text set


# --------------------------------------------------------------------------- #
# render helpers                                                              #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("tokens", "expected"),
    [
        pytest.param(["{% for x %}", "{{ y }}", "{# c #}", "plain"], {"{% for x %}", "{# c #}"}, id="mixed"),
        pytest.param(["{{ only_expr }}"], set(), id="expr-dropped"),
        pytest.param([], set(), id="empty"),
    ],
)
def test_control_tokens(tokens: list[str], expected: set[str]) -> None:
    """_control_tokens keeps {% %}/{# #} and drops {{ }} expression tags."""
    assert _control_tokens(tokens) == expected


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        pytest.param("> sub item", "\tsub item", id="sub-bullet-indented"),
        pytest.param("top item", "top item", id="top-level-unchanged"),
    ],
)
def test_format_bullet(item: str, expected: str) -> None:
    """_format_bullet indents '> ' sub-items and passes others through."""
    assert _format_bullet(item) == expected


def test_render_raises_on_surviving_control_tag(
    monkeypatch: pytest.MonkeyPatch, example_data: dict[str, Any], tmp_path: Path
) -> None:
    """The residue guard raises if a template control tag fails to render."""
    # the module is reached via sys.modules because the `render` function shadows it
    render_mod = sys.modules["hotel_report.render"]
    monkeypatch.setattr(render_mod, "find_residue", lambda _p: ["{%p for hotel in hotels %}"])
    with pytest.raises(RenderError, match="unrendered template tokens"):
        render_fn(example_data, tmp_path / "x.docx")


# --------------------------------------------------------------------------- #
# cli._force_utf8_streams                                                      #
# --------------------------------------------------------------------------- #
class _Stream:
    """A stand-in stream whose reconfigure records the encoding or raises."""

    def __init__(self, *, raises: bool = False) -> None:
        """Create a fake stream; ``raises=True`` makes reconfigure blow up."""
        self.raises = raises
        self.encoding: str | None = None

    def reconfigure(self, *, encoding: str) -> None:
        """Record the requested encoding, or raise to exercise the guard."""
        if self.raises:
            raise ValueError("cannot reconfigure")
        self.encoding = encoding


def test_force_utf8_reconfigures_when_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Streams that support reconfigure are switched to UTF-8."""
    stream = _Stream()
    monkeypatch.setattr(cli.sys, "stdout", stream)
    monkeypatch.setattr(cli.sys, "stderr", stream)
    cli._force_utf8_streams()
    assert stream.encoding == "utf-8"


def test_force_utf8_tolerates_missing_and_raising(monkeypatch: pytest.MonkeyPatch) -> None:
    """A stream without reconfigure is skipped; a raising one is swallowed."""
    monkeypatch.setattr(cli.sys, "stdout", object())  # no reconfigure attr
    monkeypatch.setattr(cli.sys, "stderr", _Stream(raises=True))
    cli._force_utf8_streams()  # must not raise
