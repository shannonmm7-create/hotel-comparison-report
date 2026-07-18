"""Snapshot test (syrupy) of the public JSON Schema."""

from __future__ import annotations

from syrupy.assertion import SnapshotAssertion

from hotel_report.schema import json_schema


def test_json_schema_snapshot(snapshot: SnapshotAssertion) -> None:
    """The generated JSON Schema (the public contract) must not change unnoticed."""
    assert json_schema() == snapshot
