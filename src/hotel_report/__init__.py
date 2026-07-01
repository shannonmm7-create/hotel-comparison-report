"""Deterministically render the JC Room Blocks Hotel Comparison Report .docx from JSON.

The public API: build a :class:`~hotel_report.models.Report` (or a dict that parses
into one) and call :func:`~hotel_report.render.render`.
"""

from hotel_report.models import Hotel, Report, Room, TripAdvisor
from hotel_report.render import RenderError, render
from hotel_report.schema import json_schema, validation_errors

__all__ = [
    "render",
    "RenderError",
    "validation_errors",
    "json_schema",
    "Report",
    "Hotel",
    "Room",
    "TripAdvisor",
    "__version__",
]
__version__ = "0.1.0"
