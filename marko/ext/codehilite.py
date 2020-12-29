r"""
Code highlight extension
~~~~~~~~~~~~~~~~~~~~~~~~

Enable code highlight using ``pygments``. This requires to install `codehilite` extras::

    pip install marko[codehilite]

Arguments:
    All arguments are passed to ``pygments.formatters.html.HtmlFormatter``.

Usage::

    from marko import Markdown

    markdown = Markdown(extensions=['codehilite'])
    markdown.convert(```python my_script.py\nprint('hello world')\n```)
"""
import json

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import html
from pygments.util import ClassNotFound


def _parse_extras(line):
    if not line:
        return {}
    return {k: json.loads(v) for part in line.split(",") for k, v in [part.split("=")]}


class CodeHiliteRendererMixin:
    options = {}  # type: dict

    def render_fenced_code(self, element):
        code = element.children[0].children
        options = CodeHiliteRendererMixin.options.copy()
        options.update(_parse_extras(getattr(element, "extra", None)))
        if element.lang:
            try:
                lexer = get_lexer_by_name(element.lang, stripall=True)
            except ClassNotFound:
                lexer = guess_lexer(code)
        else:
            lexer = guess_lexer(code)
        formatter = html.HtmlFormatter(**options)
        return highlight(code, lexer, formatter)


class CodeHilite:
    def __init__(self, **options):
        CodeHiliteRendererMixin.options = options
        self.renderer_mixins = [CodeHiliteRendererMixin]


def make_extension(**options):
    return CodeHilite(**options)
