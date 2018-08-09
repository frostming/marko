#! -*- coding: utf-8 -*-
"""
HTML renderer
"""
from .base_renderer import BaseRenderer


class HTMLRenderer(BaseRenderer):
    """The most common renderer for markdown parser"""

    def render_paragraph(self, element):
        children = self.render_children(element)
        if element._tight:
            return children
        else:
            return '<p>{}</p>\n'.format(children)

    def render_list(self, element):
        if element.ordered:
            tag = 'ol'
            extra = ' start="{}"'.format(element.start) if element.start != 1 else ''
        else:
            tag = 'ul'
            extra = ''
        return '<{tag}{extra}>\n{children}</{tag}>\n'.format(
            tag=tag, extra=extra, children=self.render_children(element)
        )

    def render_list_item(self, element):
        return '<li>\n{}</li>\n'.format(self.render_children(element))

    def render_quote(self, element):
        return '<blockquote>\n{}</blockquote>\n'.format(self.render_children(element))

    def render_fenced_code(self, element):
        lang = ' class="language-{}"'.format(element.lang) if element.lang else ''
        return '<pre><code{}>\n{}</code></pre>\n'.format(
            lang, self.render_children(element)
        )

    def render_code_block(self, element):
        return '<pre><code>\n{}</code></pre>\n'.format(self.render_children(element))

    def render_html_block(self, element):
        return element.children

    def render_thematic_break(self, element):
        return '<hr />\n'

    def render_heading(self, element):
        return '<h{level}>{children}</h{level}>\n'.format(
            level=element.level, children=self.render_children(element)
        )

    def render_setext_heading(self, element):
        return self.render_heading(element)

    def render_blank_line(self, element):
        return ''
