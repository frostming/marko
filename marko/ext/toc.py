"""
TOC extension
~~~~~~~~~~~~~

Renders the TOC(Table Of Content) for a markdown document.

Usage::

    from marko import Parser, HTMLRenderer, Markdown

    class MyParser(TocParserMixin, Parser):
        pass

    class MyRenderer(TocRendererMixin, HTMLRenderer):
        pass

    markdown = Markdown(MyParser, MyRenderer)
    print(markdown(text))
    print(markdown.renderer.render_toc())
"""
from marko import block, inline
from marko.helpers import normalize_label


class Heading(block.Heading):

    def __init__(self, *args):
        super(Heading, self).__init__(*args)
        if not hasattr(inline._root_node, 'headings'):
            inline._root_node.headings = []
        inline._root_node.headings.append((int(self.level), self.children))


class SetextHeading(block.SetextHeading):

    def __init__(self, *args):
        super(Heading, self).__init__(*args)
        if not hasattr(inline._root_node, 'headings'):
            inline._root_node.headings = []
        inline._root_node.headings.append((int(self.level), self.children))


class TocParserMixin(object):

    def __init__(self, *extras):
        super(TocParserMixin, self).__init__(*extras)

        self.add_element(Heading, True)
        self.add_element(SetextHeading, True)


class TocRendererMixin(object):

    def render_toc(self, maxlevel=3):
        first_level = None
        last_level = None
        rv = []
        for level, text in self.root_node.headings:
            if level > maxlevel:
                continue

            if first_level is None:
                first_level = level
                last_level = level
                rv.append(self._open_heading_group())

            if last_level == level - 1:
                rv.append(self._open_heading_group())
                last_level = level
            while last_level > level:
                rv.append(self._close_heading_group())
                last_level -= 1
            # last_level == level
            rv.append(self._render_toc_item(text))

        for _ in range(first_level, last_level + 1):
            rv.append(self._close_heading_group())

        return ''.join(rv)

    def _open_heading_group(self):
        return '<ul>\n'

    def _close_heading_group(self):
        return '</ul>\n'

    def _render_toc_item(self, text):
        return '<li><a href="#{}">{}</a></li>\n'.format(
            self.escape_url(normalize_label(text)), self.escape_html(text)
        )

    def render_heading(self, element):
        children = self.render_children(element)
        return '<h{0} id="{1}">{2}</h{0}>\n'.format(
            element.level, self.escape_url(normalize_label(children)), children
        )
