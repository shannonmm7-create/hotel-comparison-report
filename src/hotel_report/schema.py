"""Validate report data and expose the JSON Schema — both backed by the Pydantic
models in :mod:`hotel_report.models` (the single source of truth)."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from hotel_report._validate import validated
from hotel_report.models import Report


@validated
def validation_errors(data: object) -> list[str]:
    """Return human-readable validation errors for ``data``.

    An empty list means the data is a valid :class:`~hotel_report.models.Report`.
    Each error is ``"<field/path>: <message>"`` so the offending field is obvious.
    """
    try:
        Report.model_validate(data)
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            loc = "/".join(str(part) for part in err["loc"]) or "(root)"
            errors.append(f"{loc}: {err['msg']}")
        return errors
    return []


@validated
def json_schema() -> dict[str, Any]:
    """The JSON Schema (draft 2020-12) generated from the Pydantic models."""
    return Report.model_json_schema()
