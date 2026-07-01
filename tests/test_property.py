"""Property-based tests (hypothesis)."""

from __future__ import annotations

import copy

from hypothesis import given
from hypothesis import strategies as st

from conftest import MINIMAL
from hotel_report.render import usd
from hotel_report.schema import validation_errors


@given(st.integers(min_value=0, max_value=10**9))
def test_usd_integer_formatting(n: int) -> None:
    """For any non-negative integer, usd() prefixes '$' and preserves the digits."""
    out = usd(n)
    assert out.startswith("$")
    assert out[1:].replace(",", "") == str(n)


@given(st.sampled_from(["prepared_for", "arrival_date", "departure_date", "venue_name", "hotels"]))
def test_missing_any_required_top_level_field_is_invalid(field: str) -> None:
    """Dropping any required top-level field always yields a validation error."""
    data = copy.deepcopy(MINIMAL)
    del data[field]
    assert validation_errors(data)
