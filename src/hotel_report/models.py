"""Typed data contract for the Hotel Comparison Report.

These Pydantic v2 models **are** the contract between a data source and the
renderer: build a :class:`Report` (or a plain ``dict`` that parses into one) and
:func:`hotel_report.render.render` fills the approved Word template from it. The
JSON Schema published by ``hotel-report schema`` is generated from these models
(:meth:`pydantic.BaseModel.model_json_schema`), so there is a single source of
truth and nothing to keep in sync.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

#: A string that must contain at least one character.
NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]

#: A nightly rate: a number (rendered as ``$1,234``) or a pre-formatted string
#: such as ``"Waived"`` (passed through verbatim by the ``usd`` filter).
Rate = int | float | str


def _require_http_url(value: str) -> str:
    """Reject any URL that is not ``http://`` or ``https://`` (kept as a plain
    string so the value is never normalized — it goes verbatim into a hyperlink)."""
    if not value.startswith(("http://", "https://")):
        raise ValueError("must be an http:// or https:// URL")
    return value


#: A non-empty ``http(s)`` URL, validated but never rewritten.
HttpUrlStr = Annotated[str, StringConstraints(min_length=1), AfterValidator(_require_http_url)]


class TripAdvisor(BaseModel):
    """A hotel's TripAdvisor ranking line. If ``url`` is given, ``text`` renders as a hyperlink."""

    model_config = ConfigDict(extra="forbid")

    text: NonEmptyStr = Field(description="Display text, e.g. '#4 of 45 hotels in Charleston'.")
    url: HttpUrlStr | None = Field(default=None, description="If present, the text becomes a hyperlink to this URL.")


class Room(BaseModel):
    """One row of a hotel's negotiated-rate table."""

    model_config = ConfigDict(extra="forbid")

    room_type: NonEmptyStr = Field(description="Room category name, e.g. 'King Room'.")
    offered_rate: Rate = Field(description="Negotiated nightly rate (number -> $1,234, or a string like 'Waived').")
    rack_rate: Rate = Field(description="Standard 'rack' nightly rate (number or string).")


class Hotel(BaseModel):
    """A single hotel block; the template repeats one of these per entry."""

    model_config = ConfigDict(extra="forbid")

    name: NonEmptyStr = Field(description="Hotel name.")
    website_url: HttpUrlStr | None = Field(
        default=None, description="If present, the hotel name becomes a hyperlink to this URL."
    )
    address_line_1: NonEmptyStr = Field(description="Street address.")
    city_state_zip: NonEmptyStr = Field(description="City, state and ZIP, e.g. 'Charleston, SC 29403'.")
    tripadvisor: TripAdvisor | None = Field(default=None, description="Optional TripAdvisor ranking line.")
    rooms: list[Room] = Field(min_length=1, description="Rate-table rows; the template repeats one row per entry.")
    features: list[str] = Field(default_factory=list, description="Hotel Features bullets (full text of each bullet).")
    concessions: list[str] = Field(default_factory=list, description="Concessions bullets.")
    contracting_options: list[str] = Field(default_factory=list, description="Contracting Option bullets.")
    distance_from_venue: NonEmptyStr = Field(
        description="Full distance text incl. units, e.g. '8.1 miles' or 'Across the street'."
    )
    cutoff: NonEmptyStr = Field(description="Full cut-off text, e.g. '30 days prior to arrival, by March 17, 2027'.")


class Report(BaseModel):
    """Top-level Hotel Comparison Report data — the root of the contract."""

    model_config = ConfigDict(extra="forbid")

    prepared_for: NonEmptyStr = Field(description="Client / event name, e.g. 'Rivera-Okafor Wedding'.")
    arrival_date: NonEmptyStr = Field(description="Human-readable arrival date, e.g. 'May 14, 2027'.")
    departure_date: NonEmptyStr = Field(description="Human-readable departure date, e.g. 'May 16, 2027'.")
    venue_name: NonEmptyStr = Field(description="Event venue; shared by all hotels (distances are measured from it).")
    hotels: list[Hotel] = Field(min_length=1, description="One entry per hotel.")
