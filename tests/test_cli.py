"""Tests for the command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from conftest import SOURCE_TEMPLATE
from hotel_report.cli import main
from hotel_report.render import usd


def test_schema_command_prints_valid_json(capsys: pytest.CaptureFixture[str]) -> None:
    """`schema` prints the JSON Schema generated from the models."""
    assert main(["schema"]) == 0
    schema = json.loads(capsys.readouterr().out)
    assert "prepared_for" in schema["properties"]
    assert "hotels" in schema["properties"]


def test_validate_command_ok(tmp_path: Path, example_data: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    """`validate` reports OK for valid data."""
    path = tmp_path / "data.json"
    path.write_text(json.dumps(example_data), encoding="utf-8")
    assert main(["validate", str(path)]) == 0
    assert "OK" in capsys.readouterr().out


def test_validate_command_reports_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`validate` reports errors and returns 1 for invalid data."""
    path = tmp_path / "bad.json"
    path.write_text('{"prepared_for": "x", "hotels": []}', encoding="utf-8")
    assert main(["validate", str(path)]) == 1
    assert "INVALID" in capsys.readouterr().out


def test_missing_file_exits() -> None:
    """A missing data file exits with a friendly message, not a traceback."""
    with pytest.raises(SystemExit) as exc:
        main(["validate", "/no/such/file.json"])
    assert "no such file" in str(exc.value)


def test_invalid_json_exits(tmp_path: Path) -> None:
    """A malformed JSON file exits with a friendly message."""
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        main(["validate", str(path)])
    assert "not valid JSON" in str(exc.value)


def test_render_command(tmp_path: Path, example_data: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    """`render` writes a .docx and reports the counts."""
    data = tmp_path / "data.json"
    data.write_text(json.dumps(example_data), encoding="utf-8")
    out = tmp_path / "report.docx"
    assert main(["render", str(data), str(out)]) == 0
    assert out.exists()
    assert "3 hotel(s)" in capsys.readouterr().out


def test_render_command_reports_validation_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`render` on invalid data prints the errors and returns 1 (no --no-validate)."""
    data = tmp_path / "bad.json"
    data.write_text('{"prepared_for": "x", "hotels": []}', encoding="utf-8")
    out = tmp_path / "out.docx"
    assert main(["render", str(data), str(out)]) == 1
    assert "Fix these" in capsys.readouterr().out


def test_render_no_validate_with_invalid_data_exits(tmp_path: Path) -> None:
    """`render --no-validate` on structurally invalid data exits cleanly (the
    model still validates and the ValidationError is caught)."""
    data = tmp_path / "bad.json"
    data.write_text('{"prepared_for": "x", "hotels": []}', encoding="utf-8")
    out = tmp_path / "out.docx"
    with pytest.raises(SystemExit):
        main(["render", str(data), str(out), "--no-validate"])


def test_example_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """`example` with no path prints the example JSON."""
    assert main(["example"]) == 0
    assert "prepared_for" in capsys.readouterr().out


def test_example_to_file(tmp_path: Path) -> None:
    """`example <path>` writes the example JSON to a file."""
    out = tmp_path / "ex.json"
    assert main(["example", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["hotels"]


def test_build_template_command(tmp_path: Path) -> None:
    """`build-template` regenerates a Jinja template from the source .docx."""
    out = tmp_path / "tpl.docx"
    assert main(["build-template", SOURCE_TEMPLATE, str(out)]) == 0
    assert out.exists()


def test_bad_template_exits_cleanly(tmp_path: Path, example_data: dict[str, Any]) -> None:
    """A missing --template exits with a friendly message, not a raw traceback."""
    data = tmp_path / "data.json"
    data.write_text(json.dumps(example_data), encoding="utf-8")
    out = tmp_path / "out.docx"
    with pytest.raises(SystemExit) as exc:
        main(["render", str(data), str(out), "--template", str(tmp_path / "nope.docx")])
    assert "error:" in str(exc.value)


def test_example_creates_parent_dirs(tmp_path: Path) -> None:
    """`example` writes to a nested path, creating parent directories."""
    out = tmp_path / "nested" / "deep" / "ex.json"
    assert main(["example", str(out)]) == 0
    assert out.exists()


def test_validate_call_enforces_signatures() -> None:
    """@validated (pydantic.validate_call) rejects a wrongly-typed argument."""
    with pytest.raises(ValidationError):
        usd([1, 2, 3])  # type: ignore[arg-type]  # not float | int | str
