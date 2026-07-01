"""Table-driven tests for schema validation error reporting."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from hotel_report.schema import validation_errors

_DELETE = object()  # sentinel: remove the key instead of setting it


def _mutate(data: dict[str, Any], path: tuple[Any, ...], value: Any) -> None:
    """Set ``data[path[0]][path[1]]… = value`` (or delete the leaf if value is _DELETE)."""
    target = data
    for key in path[:-1]:
        target = target[key]
    if value is _DELETE:
        del target[path[-1]]
    else:
        target[path[-1]] = value


@pytest.mark.parametrize(
    ("path", "value", "needle"),
    [
        pytest.param(("venue_name",), _DELETE, "venue_name", id="missing-required-top-level"),
        pytest.param(("hotels",), [], "hotels", id="empty-hotels-list"),
        pytest.param(("hotels", 0, "rooms", 0, "offered_rate"), _DELETE, "offered_rate", id="room-missing-rate"),
        pytest.param(("hotels", 0, "surprise"), "x", "surprise", id="unknown-field-forbidden"),
        pytest.param(("hotels", 0, "cutoff"), "", "cutoff", id="empty-cutoff"),
        pytest.param(("hotels", 0, "distance_from_venue"), "", "distance_from_venue", id="empty-distance"),
        pytest.param(("hotels", 0, "tripadvisor", "text"), "", "tripadvisor", id="empty-tripadvisor-text"),
        pytest.param(("hotels", 0, "website_url"), "not-a-url", "website_url", id="bad-website-url"),
    ],
)
def test_invalid_data_is_reported(example_data: dict[str, Any], path: tuple[Any, ...], value: Any, needle: str) -> None:
    """Each invalid mutation yields an error mentioning the offending field."""
    data = copy.deepcopy(example_data)
    _mutate(data, path, value)
    errors = validation_errors(data)
    assert any(needle in err for err in errors), errors


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param((), None, id="unchanged-example"),
        pytest.param(("hotels", 0, "rooms", 0, "offered_rate"), "Waived", id="string-rate"),
        pytest.param(("hotels", 0, "distance_from_venue"), "Across the street", id="free-form-distance"),
        pytest.param(("hotels", 0, "tripadvisor"), None, id="tripadvisor-omitted"),
    ],
)
def test_valid_data_passes(example_data: dict[str, Any], path: tuple[Any, ...], value: Any) -> None:
    """Each valid variation of the example produces no errors."""
    data = copy.deepcopy(example_data)
    if path:
        _mutate(data, path, value)
    assert validation_errors(data) == []
