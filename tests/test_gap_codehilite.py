"""Gap tests for the codehilite extension (requires pygments).

Existing coverage (test_ext.py): fenced/indented rendering, linenos=table,
filename extra. This file covers the no-language and unknown-language
fallbacks and the linenos=inline option. Skipped when pygments is absent,
since codehilite is an optional extra.
"""

import pytest

pygments = pytest.importorskip("pygments")

from marko import Markdown
from marko.ext.codehilite import make_extension

CH = Markdown(extensions=["codehilite"])


def test_codehilite_no_language_still_highlights():
    out = CH("```\nx\n```\n")
    assert '<div class="highlight">' in out


def test_codehilite_unknown_language_falls_back_gracefully():
    out = CH("```zzzznotalang\nx\n```\n")
    assert '<div class="highlight">' in out
    assert "zzzznotalang" not in out


def test_codehilite_filename_extra_without_other_options():
    out = CH('```python filename="test.py"\nx\n```\n')
    assert '<span class="filename">test.py</span>' in out


def test_codehilite_linenos_inline():
    md = Markdown(extensions=[make_extension(linenos="inline")])
    out = md("```python\nx\n```\n")
    assert '<span class="linenos">1</span>' in out
