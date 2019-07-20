# -*- coding: utf-8 -*-
"""
TOC extension
~~~~~~~~~~~~~

Renders the TOC(Table Of Content) for a markdown document.

Usage::

    from marko import Markdown

    markdown = Markdown(extensions=[TocExtension])

    print(markdown(text))
    print(markdown.renderer.render_toc())
"""
from __future__ import unicode_literals
from slugify import slugify  # type: ignore
import re


class TocRendererMixin(object):
    def __enter__(self):
        self.headings = []
        return super(TocRendererMixin, self).__enter__()

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
                rv.append(self._open_heading_group())

            if last_level == level - 1:
                rv.append(self._open_heading_group())
                last_level = level
            while last_level > level:
                rv.append(self._close_heading_group())
                last_level -= 1
            # last_level == level
            rv.append(self._render_toc_item(slug, text))
        for _ in range(first_level, last_level + 1):
            rv.append(self._close_heading_group())

        return "".join(rv)

    def _open_heading_group(self):
        return "<ul>\n"

    def _close_heading_group(self):
        return "</ul>\n"

    def _render_toc_item(self, slug, text):
        return '<li><a href="#{}">{}</a></li>\n'.format(slug, self.escape_html(text))

    def render_heading(self, element):
        children = self.render_children(element)
        slug = slugify(re.sub(r"<.+?>", "", children))
        self.headings.append((int(element.level), slug, children))
        return '<h{0} id="{1}">{2}</h{0}>\n'.format(element.level, slug, children)


class TocExtension:
    renderer_mixins = [TocRendererMixin]
