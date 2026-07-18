"""Command-line interface: ``hotel-report <command>``.

This CLI is the uniform entry point every agent (Claude, Copilot, Codex) and
human uses. Always invoke it through uv so the locked environment is used:

    uv run hotel-report example  my_report.json          # scaffold a data file
    uv run hotel-report validate my_report.json          # check the schema
    uv run hotel-report render   my_report.json out.docx # produce the .docx
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path
from typing import Any

from docx.opc.exceptions import PackageNotFoundError
from pydantic import ValidationError

from hotel_report import __version__
from hotel_report._validate import validated
from hotel_report.build_template import build
from hotel_report.render import RenderError, render
from hotel_report.schema import json_schema, validation_errors

EXAMPLE_RESOURCE = files("hotel_report").joinpath("data/example_report.json")


@validated
def _load(path: str) -> Any:
    """Load a JSON file, exiting with a friendly message on error."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        sys.exit(f"error: no such file: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path} is not valid JSON: {exc}")


@validated
def _print_errors(errors: list[str]) -> None:
    """Print a list of validation errors as a bulleted 'INVALID' block."""
    print(f"INVALID ({len(errors)} error(s)):")
    for err in errors:
        print(f"  - {err}")


@validated
def _cmd_validate(args: argparse.Namespace) -> int:
    """Validate a data file against the schema."""
    errors = validation_errors(_load(args.data))
    if errors:
        _print_errors(errors)
        return 1
    print("OK: data matches the schema.")
    return 0


@validated
def _cmd_render(args: argparse.Namespace) -> int:
    """Validate (unless --no-validate) then render the report .docx."""
    data = _load(args.data)
    if not args.no_validate:
        errors = validation_errors(data)
        if errors:
            print("Fix these or pass --no-validate:")
            _print_errors(errors)
            return 1
    try:
        summary = render(data, args.output, template=args.template)
    except (RenderError, ValidationError, FileNotFoundError, PackageNotFoundError) as exc:
        sys.exit(f"error: {exc}")
    print(f"wrote {summary['output']}  ({summary['hotels']} hotel(s), {summary['rooms']} room row(s))")
    return 0


@validated
def _cmd_schema(args: argparse.Namespace) -> int:  # pylint: disable=unused-argument  # uniform CLI dispatch signature
    """Print the JSON Schema generated from the Pydantic models."""
    print(json.dumps(json_schema(), indent=2))
    return 0


@validated
def _cmd_example(args: argparse.Namespace) -> int:
    """Print, or write to a file, the bundled example data."""
    content = EXAMPLE_RESOURCE.read_text(encoding="utf-8")
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(content)
    return 0


@validated
def _cmd_build_template(args: argparse.Namespace) -> int:
    """Regenerate the Jinja template from a client source .docx."""
    out = build(args.source, args.output)
    print(f"wrote {out}")
    return 0


@validated
def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the ``hotel-report`` command."""
    parser = argparse.ArgumentParser(prog="hotel-report", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a data JSON file against the schema")
    validate.add_argument("data")
    validate.set_defaults(func=_cmd_validate)

    render_cmd = sub.add_parser("render", help="validate then render the report .docx")
    render_cmd.add_argument("data")
    render_cmd.add_argument("output")
    render_cmd.add_argument("--template", help="override the packaged template (.docx)")
    render_cmd.add_argument("--no-validate", action="store_true", help="skip the pre-render schema check")
    render_cmd.set_defaults(func=_cmd_render)

    schema = sub.add_parser("schema", help="print the JSON Schema (the data contract)")
    schema.set_defaults(func=_cmd_schema)

    example = sub.add_parser("example", help="print or write the example data file")
    example.add_argument("output", nargs="?", help="write here instead of stdout")
    example.set_defaults(func=_cmd_example)

    build_template = sub.add_parser("build-template", help="regenerate the Jinja template from a source .docx")
    build_template.add_argument("source", help="client source .docx (placeholder text)")
    build_template.add_argument("output", help="destination Jinja template .docx")
    build_template.set_defaults(func=_cmd_build_template)

    return parser


@validated
def _force_utf8_streams() -> None:
    """Best-effort UTF-8 stdout/stderr so en/em dashes don't crash a legacy console."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except ValueError, OSError:
                pass


@validated
def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``hotel-report`` console script."""
    _force_utf8_streams()
    args = build_parser().parse_args(argv)
    func: Any = args.func
    return int(func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
