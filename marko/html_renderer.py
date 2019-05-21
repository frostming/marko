#! -*- coding: utf-8 -*-
"""
HTML renderer
"""
from __future__ import unicode_literals
import re

from ._compat import string_types, html, quote
from .renderer import Renderer


class HTMLRenderer(Renderer):
    """The most common renderer for markdown parser"""

    _charref = re.compile(
        r"&(#[0-9]{1,8};" r"|#[xX][0-9a-fA-F]{1,8};" r"|[^\t\n\f <&#;]{1,32};)"
    )

    def __enter__(self):
        # commonmark spec doesn't respect char refs without ';' as end.
        self._charref_bak = html._charref
        html._charref = self._charref
        return super(HTMLRenderer, self).__enter__()

    def __exit__(self, *args):
        html._charref = self._charref_bak
        return super(HTMLRenderer, self).__exit__(*args)

    def render_paragraph(self, element):
        children = self.render_children(element)
        if element._tight:
            return children
        else:
            return "<p>{}</p>\n".format(children)

    def render_list(self, element):
        if element.ordered:
            tag = "ol"
            extra = ' start="{}"'.format(element.start) if element.start != 1 else ""
        else:
            tag = "ul"
            extra = ""
        return "<{tag}{extra}>\n{children}</{tag}>\n".format(
            tag=tag, extra=extra, children=self.render_children(element)
        )

    def render_list_item(self, element):
        if len(element.children) == 1 and getattr(element.children[0], "_tight", False):
            sep = ""
        else:
            sep = "\n"
        return "<li>{}{}</li>\n".format(sep, self.render_children(element))

    def render_quote(self, element):
        return "<blockquote>\n{}</blockquote>\n".format(self.render_children(element))

    def render_fenced_code(self, element):
        lang = ' class="language-{}"'.format(element.lang) if element.lang else ""
        return "<pre><code{}>{}</code></pre>\n".format(
            lang, html.escape(element.children[0].children)
        )

    def render_code_block(self, element):
        return self.render_fenced_code(element)

    def render_html_block(self, element):
        return element.children

    def render_thematic_break(self, element):
        return "<hr />\n"

    def render_heading(self, element):
        return "<h{level}>{children}</h{level}>\n".format(
            level=element.level, children=self.render_children(element)
        )

    def render_setext_heading(self, element):
        return self.render_heading(element)

    def render_blank_line(self, element):
        return ""

    def render_link_ref_def(self, elemement):
        return ""

    def render_emphasis(self, element):
        return "<em>{}</em>".format(self.render_children(element))

    def render_strong_emphasis(self, element):
        return "<strong>{}</strong>".format(self.render_children(element))

    def render_inline_html(self, element):
        return self.render_html_block(element)

    def render_plain_text(self, element):
        if isinstance(element.children, string_types):
            return self.escape_html(element.children)
        return self.render_children(element)

    def render_link(self, element):
        template = '<a href="{}"{}>{}</a>'
        title = (
            ' title="{}"'.format(self.escape_html(element.title))
            if element.title
            else ""
        )
        url = self.escape_url(element.dest)
        body = self.render_children(element)
        return template.format(url, title, body)

    def render_auto_link(self, element):
        return self.render_link(element)

    def render_image(self, element):
        template = '<img src="{}" alt="{}"{} />'
        title = (
            ' title="{}"'.format(self.escape_html(element.title))
            if element.title
            else ""
        )
        url = self.escape_url(element.dest)
        render_func = self.render
        self.render = self.render_plain_text
        body = self.render_children(element)
        self.render = render_func
        return template.format(url, body, title)

    def render_literal(self, element):
        return self.render_raw_text(element)

    def render_raw_text(self, element):
        return self.escape_html(element.children)

    def render_line_break(self, element):
        if element.soft:
            return "\n"
        return "<br />\n"

    def render_code_span(self, element):
        return "<code>{}</code>".format(html.escape(element.children))

    @staticmethod
    def escape_html(raw):
        return html.escape(html.unescape(raw)).replace("&#x27;", "'")

    @staticmethod
    def escape_url(raw):
        """
        Escape urls to prevent code injection craziness. (Hopefully.)
        """
        return html.escape(quote(html.unescape(raw), safe="/#:()*?=%@+,&"))
