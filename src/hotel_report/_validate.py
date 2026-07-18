"""The shared ``@validated`` decorator.

It wraps a function with Pydantic's :func:`pydantic.validate_call`, which checks
every argument against the function's type hints **at call time** and raises a
``ValidationError`` on a mismatch. ``arbitrary_types_allowed=True`` lets
python-docx / docxtpl / lxml objects (which have no pydantic schema) pass through
as plain instance checks; OOXML element parameters are annotated ``Any``, so they
are passed through untouched — important, since several helpers mutate them.
"""

from __future__ import annotations

from pydantic import ConfigDict, validate_call

validated = validate_call(config=ConfigDict(arbitrary_types_allowed=True))
