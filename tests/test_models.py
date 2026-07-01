"""Tests for the Pydantic data models."""

from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from conftest import MINIMAL
from hotel_report.models import Report, Room
from hotel_report.schema import json_schema


def test_example_parses_into_model(example_data: dict) -> None:
    """The example parses into a fully typed Report."""
    report = Report.model_validate(example_data)
    assert len(report.hotels) == 3  # noqa: PLR2004
    assert isinstance(report.hotels[0].rooms[0], Room)
    # optional lists default to empty, not None
    assert report.hotels[0].features


def test_minimal_is_valid() -> None:
    """The minimal report is valid."""
    Report.model_validate(MINIMAL)


def test_extra_fields_forbidden() -> None:
    """Unknown fields raise (extra='forbid')."""
    bad = copy.deepcopy(MINIMAL)
    bad["surprise"] = 1
    with pytest.raises(ValidationError):
        Report.model_validate(bad)


@pytest.mark.parametrize("bad_url", ["ftp://x", "", "example.com"])
def test_url_must_be_http_rejects(bad_url: str) -> None:
    """Non-http(s) / empty URLs are rejected."""
    bad = copy.deepcopy(MINIMAL)
    bad["hotels"][0]["website_url"] = bad_url
    with pytest.raises(ValidationError):
        Report.model_validate(bad)


@pytest.mark.parametrize("rate", [305, 305.5, "Waived", "$305 + tax"])
def test_rate_accepts_number_or_string(rate: float | str) -> None:
    """A rate may be a number or a pre-formatted string."""
    ok = copy.deepcopy(MINIMAL)
    ok["hotels"][0]["rooms"][0]["offered_rate"] = rate
    ok["hotels"][0]["website_url"] = "https://hotel.example.com/"  # also exercise a valid URL
    Report.model_validate(ok)


def test_json_schema_generated_from_models() -> None:
    """The generated JSON Schema reflects the model shape and extra='forbid'."""
    schema = json_schema()
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False  # from extra="forbid"
    assert {"prepared_for", "hotels"} <= set(schema["properties"])
