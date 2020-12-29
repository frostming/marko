"""
TOC extension
~~~~~~~~~~~~~

Renders the TOC(Table Of Content) for a markdown document.
This requires to install `toc` extras::

    pip install marko[toc]

Arguments:
* openning: the openning tag, defaults to <ul>
* closing: the closing tag, defaults to </ul>
* item_format: the toc item format, defaults to '<li><a href="#{slug}">{text}</a></li>'

Usage::

    from marko import Markdown

    markdown = Markdown(extensions=['toc'])

    print(markdown(text))
    print(markdown.renderer.render_toc())

"""
import re

from slugify import slugify  # type: ignore


class TocRendererMixin:
    openning = "<ul>"
    closing = "</ul>"
    item_format = '<li><a href="#{slug}">{text}</a></li>'

    def __enter__(self):
        self.headings = []
        return super().__enter__()

    def render_toc(self, maxdepth=3):
        if not self.headings:
            return ""
        first_level = None
        last_level = None
        rv = []
        for level, slug, text in self.headings:
            if first_level is not None and level >= first_level + maxdepth:
                continue

            if first_level is None:
                first_level = level
                last_level = level
                rv.append(TocRendererMixin.openning + "\n")

            if last_level == level - 1:
                rv.append(TocRendererMixin.openning + "\n")
                last_level = level
            while last_level > level:
                rv.append(TocRendererMixin.closing + "\n")
                last_level -= 1
            # last_level == level
            rv.append(TocRendererMixin.item_format.format(slug=slug, text=text) + "\n")
        for _ in range(first_level, last_level + 1):
            rv.append(TocRendererMixin.closing + "\n")

        return "".join(rv)

    def render_heading(self, element):
        children = self.render_children(element)
        slug = slugify(re.sub(r"<.+?>", "", children))
        self.headings.append((int(element.level), slug, children))
        return '<h{0} id="{1}">{2}</h{0}>\n'.format(element.level, slug, children)


class Toc:
    def __init__(self, openning=None, closing=None, item_format=None):
        if openning:
            TocRendererMixin.openning = openning
        if closing:
            TocRendererMixin.closing = closing
        if item_format:
            TocRendererMixin.item_format = item_format
        self.renderer_mixins = [TocRendererMixin]


def make_extension(openning=None, closing=None, item_format=None):
    return Toc(openning, closing, item_format)
