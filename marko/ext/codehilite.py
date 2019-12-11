r"""
Code highlight extension
~~~~~~~~~~~~~~~~~~~~~~~~

Enable code highlight using ``pygments``. This requires to install `codehilite` extras::

    pip install marko[codehilite]

Usage::

    from marko import Markdown

    markdown = Markdown(extensions=['codehilite'])
    markdown.convert(```python my_script.py\nprint('hello world')\n```)
"""
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
from pygments.util import ClassNotFound


class CodeHiliteRendererMixin(object):

    def render_fenced_code(self, element):
        if element.lang:
            try:
                lexer = get_lexer_by_name(element.lang, stripall=True)
            except ClassNotFound:
                pass
            else:
                formatter = html.HtmlFormatter()
                return highlight(element.children[0].children, lexer, formatter)
        return super(CodeHiliteRendererMixin, self).render_fenced_code(element)


class CodeHilite(object):
    renderer_mixins = [CodeHiliteRendererMixin]
