"""Load and validate report data against the JSON Schema contract."""
from __future__ import annotations

import json
from importlib.resources import files

from jsonschema import Draft202012Validator

SCHEMA_RESOURCE = files("hotel_report").joinpath("schema/report.schema.json")


def load_schema() -> dict:
    with SCHEMA_RESOURCE.open(encoding="utf-8") as fh:
        return json.load(fh)


def validation_errors(data) -> list[str]:
    """Return a list of human-readable validation errors ([] means valid)."""
    validator = Draft202012Validator(load_schema())
    out = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        out.append(f"{loc}: {err.message}")
    return out
