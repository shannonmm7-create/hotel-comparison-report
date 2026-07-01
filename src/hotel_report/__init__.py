"""Deterministically render the JC Room Blocks Hotel Comparison Report .docx from JSON."""
from hotel_report.render import RenderError, render
from hotel_report.schema import load_schema, validation_errors

__all__ = ["render", "RenderError", "validation_errors", "load_schema", "__version__"]
__version__ = "0.1.0"
