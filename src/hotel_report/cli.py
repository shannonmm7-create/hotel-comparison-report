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

from hotel_report import __version__
from hotel_report.render import RenderError, render
from hotel_report.schema import SCHEMA_RESOURCE, validation_errors

EXAMPLE_RESOURCE = files("hotel_report").joinpath("data/example_report.json")


def _load(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        sys.exit(f"error: no such file: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path} is not valid JSON: {exc}")


def _cmd_validate(args) -> int:
    errors = validation_errors(_load(args.data))
    if errors:
        print(f"INVALID ({len(errors)} error(s)):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK: data matches the schema.")
    return 0


def _cmd_render(args) -> int:
    data = _load(args.data)
    errors = validation_errors(data)
    if errors and not args.no_validate:
        print(f"INVALID ({len(errors)} error(s)) — fix these or pass --no-validate:")
        for e in errors:
            print(f"  - {e}")
        return 1
    try:
        summary = render(data, args.output, template=args.template)
    except RenderError as exc:
        sys.exit(f"error: {exc}")
    print(f"wrote {summary['output']}  ({summary['hotels']} hotel(s), {summary['rooms']} room row(s))")
    return 0


def _cmd_schema(args) -> int:
    print(SCHEMA_RESOURCE.read_text(encoding="utf-8"))
    return 0


def _cmd_example(args) -> int:
    content = EXAMPLE_RESOURCE.read_text(encoding="utf-8")
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(content)
    return 0


def _cmd_build_template(args) -> int:
    from hotel_report.build_template import build

    out = build(args.source, args.output)
    print(f"wrote {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hotel-report", description=__doc__)
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate a data JSON file against the schema")
    v.add_argument("data")
    v.set_defaults(func=_cmd_validate)

    r = sub.add_parser("render", help="validate then render the report .docx")
    r.add_argument("data")
    r.add_argument("output")
    r.add_argument("--template", help="override the packaged template (.docx)")
    r.add_argument("--no-validate", action="store_true", help="skip schema validation")
    r.set_defaults(func=_cmd_render)

    s = sub.add_parser("schema", help="print the JSON Schema (the data contract)")
    s.set_defaults(func=_cmd_schema)

    e = sub.add_parser("example", help="print or write the example data file")
    e.add_argument("output", nargs="?", help="write here instead of stdout")
    e.set_defaults(func=_cmd_example)

    b = sub.add_parser("build-template", help="regenerate the Jinja template from a source .docx")
    b.add_argument("source", help="client source .docx (placeholder text)")
    b.add_argument("output", help="destination Jinja template .docx")
    b.set_defaults(func=_cmd_build_template)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
