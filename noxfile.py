"""Task runner. Run with ``uv run nox`` (default sessions) or ``uv run nox -s <name>``.

Sessions run in the active uv-managed environment (``venv_backend="none"``), so
they use the exact locked toolchain rather than creating separate venvs.
"""

import nox

nox.options.default_venv_backend = "none"
nox.options.sessions = [
    "lint",
    "format_check",
    "typecheck",
    "pylint",
    "docstrings",
    "security",
    "spelling",
    "tests",
]


@nox.session
def lint(session: nox.Session) -> None:
    """ruff (lint only; PL ruleset included)."""
    session.run("ruff", "check", ".", external=True)


@nox.session
def format_check(session: nox.Session) -> None:
    """black --check (the formatter)."""
    session.run("black", "--check", ".", external=True)


@nox.session
def format(session: nox.Session) -> None:  # noqa: A001 - nox session name
    """black (apply formatting)."""
    session.run("black", ".", external=True)


@nox.session
def typecheck(session: nox.Session) -> None:
    """mypy static type check (src + tests, per pyproject `files`)."""
    session.run("mypy", external=True)


@nox.session
def pylint(session: nox.Session) -> None:
    """pylint semantic/design checks (slower, catches what ruff can't)."""
    session.run("pylint", "src/hotel_report", external=True)


@nox.session
def docstrings(session: nox.Session) -> None:
    """interrogate docstring-coverage gate (src + tests)."""
    session.run("interrogate", "-v", "src", "tests", external=True)


@nox.session
def security(session: nox.Session) -> None:
    """bandit security scan (reads assert_used skips from pyproject)."""
    session.run("bandit", "-c", "pyproject.toml", "-q", "-r", "src", "tests", external=True)


@nox.session
def spelling(session: nox.Session) -> None:
    """codespell over the repo."""
    session.run("codespell", external=True)


@nox.session
def tests(session: nox.Session) -> None:
    """pytest with coverage, in parallel (xdist)."""
    session.run("pytest", "-n", "auto", *session.posargs, external=True)


@nox.session
def benchmarks(session: nox.Session) -> None:
    """pytest-benchmark timings (serial, no coverage)."""
    session.run("pytest", "--benchmark-enable", "--benchmark-only", "--no-cov", external=True)


@nox.session
def mutation(session: nox.Session) -> None:
    """mutmut mutation testing (slow; run on demand)."""
    session.run("mutmut", "run", external=True)
