"""Benchmark (pytest-benchmark) of a full render."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pytest_benchmark.fixture import BenchmarkFixture

from hotel_report.render import render


def test_render_benchmark(benchmark: BenchmarkFixture, example_data: dict[str, Any], tmp_path: Path) -> None:
    """Benchmark a full render (timed only under `nox -s benchmarks`)."""
    out = tmp_path / "bench.docx"
    benchmark(render, example_data, out)
