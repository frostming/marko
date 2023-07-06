"""
A renderer for Gemtext (https://gemini.circumlunar.space/).
"""
from typing import Any, Iterator, Union, cast

from . import block, inline
from .renderer import Renderer


def extract_links(
    paragraph,
) -> Iterator[Union[inline.Link, inline.AutoLink]]:
    """Extract links from a paragraph."""
    queue = [paragraph]
    while queue:
        element = queue.pop(0)

        if isinstance(element, (inline.Link, inline.AutoLink)):
            yield element
        elif hasattr(element, "children"):
            queue.extend(element.children)


class GemtextRenderer(Renderer):

    """
    Render Markdown to Gemtext.
    """

    def render_paragraph(self, element: block.Paragraph) -> str:
        """
        Render a paragraph.

        Links are collected and displayed after the paragraph.
        """
        paragraph = self.render_children(element) + "\n"

        links = list(extract_links(element))
        if not links:
            return paragraph

        return (
            paragraph
            + "\n"
            + "\n".join(self._render_paragraph_link(link) for link in links)
            + "\n"
        )

    def _render_paragraph_link(
        self, element: Union[inline.Link, inline.AutoLink]
    ) -> str:
        if element.title:
            return f"=> {element.dest} {element.title}"

        return f"=> {element.dest} {self.render_children(element)}"

    def render_list(self, element: block.List) -> str:
        return self.render_children(element)

    def render_list_item(self, element: block.ListItem) -> str:
        return "* " + self.render_children(element)

    def render_quote(self, element: block.Quote) -> str:
        return "\n".join(
            f"> {line}" if line else ""
            for line in self.render_children(element).split("\n")
        )

    def render_fenced_code(self, element: block.FencedCode) -> str:
        """
        Render code inside triple backticks.
        """
        return "```\n" + self.render_children(element) + "```\n"

    def render_code_block(self, element: block.CodeBlock) -> str:
        return self.render_fenced_code(cast("block.FencedCode", element))

    def render_html_block(self, element: block.HTMLBlock) -> str:
        return element.body

    def render_thematic_break(self, element: block.ThematicBreak) -> str:
        return "---\n"

    def render_heading(self, element: block.Heading) -> str:
        level: int = min(element.level, 3)
        return "#" * level + " " + self.render_children(element) + "\n"

    def render_setext_heading(self, element: block.SetextHeading) -> str:
        return self.render_heading(cast("block.Heading", element))

    def render_blank_line(self, element: block.BlankLine) -> str:
        return "\n"

    def render_link_ref_def(self, element: block.LinkRefDef) -> str:
        return ""

    def render_inline_html(self, element: inline.InlineHTML) -> str:
        return str(element.children)

    def render_plain_text(self, element: Any) -> str:
        if isinstance(element.children, str):
            return element.children
        return self.render_children(element)

    def render_image(self, element: inline.Image) -> str:
        if element.title:
            return f"=> {element.dest} {element.title}"

        return f"=> {element.dest} {self.render_children(element)}"

    def render_literal(self, element: inline.Literal) -> str:
        return str(element.children)

    def render_raw_text(self, element: inline.RawText) -> str:
        return str(element.children)

    def render_line_break(self, element: inline.LineBreak) -> str:
        return "\n"

    def render_code_span(self, element: inline.CodeSpan) -> str:
        return str(element.children)
