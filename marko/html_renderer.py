"""
HTML renderer
"""
import html
from urllib.parse import quote

from .renderer import Renderer


class HTMLRenderer(Renderer):
    """The most common renderer for markdown parser"""

    def render_paragraph(self, element):
        children = self.render_children(element)
        if element._tight:
            return children
        else:
            return f"<p>{children}</p>\n"

    def render_list(self, element):
        if element.ordered:
            tag = "ol"
            extra = f' start="{element.start}"' if element.start != 1 else ""
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
        return f"<li>{sep}{self.render_children(element)}</li>\n"

    def render_quote(self, element):
        return f"<blockquote>\n{self.render_children(element)}</blockquote>\n"

    def render_fenced_code(self, element):
        lang = (
            f' class="language-{self.escape_html(element.lang)}"'
            if element.lang
            else ""
        )
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

    def render_link_ref_def(self, element):
        return ""

    def render_emphasis(self, element):
        return f"<em>{self.render_children(element)}</em>"

    def render_strong_emphasis(self, element):
        return f"<strong>{self.render_children(element)}</strong>"

    def render_inline_html(self, element):
        return self.render_html_block(element)

    def render_plain_text(self, element):
        if isinstance(element.children, str):
            return self.escape_html(element.children)
        return self.render_children(element)

    def render_link(self, element):
        template = '<a href="{}"{}>{}</a>'
        title = (
            f' title="{self.escape_html(element.title)}"'
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
            f' title="{self.escape_html(element.title)}"'
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
        return f"<code>{html.escape(element.children)}</code>"

    @staticmethod
    def escape_html(raw):
        return html.escape(html.unescape(raw)).replace("&#x27;", "'")

    @staticmethod
    def escape_url(raw):
        """
        Escape urls to prevent code injection craziness. (Hopefully.)
        """
        return html.escape(quote(html.unescape(raw), safe="/#:()*?=%@+,&"))
