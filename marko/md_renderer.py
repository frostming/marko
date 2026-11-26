"""
Markdown renderer
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, cast

from . import patterns
from .renderer import Renderer

if TYPE_CHECKING:
    from . import block, inline


# Line starts that would begin a block instead of continuing a paragraph: an ATX
# heading, a bullet list item, a thematic break, a setext underline, a block quote,
# a code fence, and a list item numbered 1 (or any number inside a container).
_BLOCK_START_RE = re.compile(
    r"#{1,6}(?=[ \t]|$)|[-+*](?=[ \t]|$)|[-*_](?=[ \t]*[-*_])|[>=]|`{3}|~{3}"
)
_ORDERED_START_RE = re.compile(r"\d{1,9}(?=[.)](?:[ \t]|$))")
# The HTML blocks that can interrupt a paragraph (types 1 to 6 of the spec)
_HTML_BLOCK_START_RE = re.compile(
    r"(?i)<(?:(?:script|pre|style|textarea)[>\s]|!--|\?|![a-z]|!\[CDATA\["
    r"|/?(?:%s)(?: +|/?>|$))" % "|".join(patterns.tags)
)


def _escape_block_start(text: str, in_container: bool = False) -> str:
    """Backslash-escape a block marker at the start of a paragraph line.

    A list item numbered other than 1 cannot interrupt a paragraph, but it can
    end the paragraph of a list item or a quote when the line is not indented.
    """
    ordered = _ORDERED_START_RE.match(text)
    if ordered and (in_container or ordered.group() == "1"):
        return text[: ordered.end()] + "\\" + text[ordered.end() :]
    if _BLOCK_START_RE.match(text) or _HTML_BLOCK_START_RE.match(text):
        return "\\" + text
    return text


class MarkdownRenderer(Renderer):
    """Render the AST back to markdown document.

    It is useful for, e.g. merging sections and formatting documents.
    For convenience, markdown renderer provides all render functions for basic elements
    and those from common extensions.
    """

    def __init__(self) -> None:
        super().__init__()
        self._prefix = ""
        self._second_prefix = ""
        self._before_code_block = False

    def __enter__(self) -> MarkdownRenderer:
        self._prefix = ""
        self._second_prefix = ""
        return super().__enter__()

    def render_children(self, element: Any) -> Any:
        rendered = []
        for index, child in enumerate(element.children):
            if child.get_type() == "List":
                # Lists of other kinds can be next to each other: all of them are
                # indented, or the indented one would be nested in the one before
                following = next(
                    (
                        sibling
                        for sibling in element.children[index + 1 :]
                        if sibling.get_type() not in ("BlankLine", "List")
                    ),
                    None,
                )
                self._before_code_block = (
                    following is not None and following.get_type() == "CodeBlock"
                )
            rendered.append(self.render(child))
        return "".join(rendered)

    @contextmanager
    def container(
        self, prefix: str, second_prefix: str = ""
    ) -> Generator[None, None, None]:
        old_prefix = self._prefix
        old_second_prefix = self._second_prefix
        self._prefix += prefix
        self._second_prefix += second_prefix
        yield
        self._prefix = old_prefix
        self._second_prefix = old_second_prefix

    def render_paragraph(self, element: block.Paragraph) -> str:
        line = self._prefix + self._render_paragraph_children(element) + "\n"
        self._prefix = self._second_prefix
        return line

    def _render_paragraph_children(
        self, element: block.Paragraph | block.SetextHeading
    ) -> str:
        parts = []
        line_start = False
        children = element.children
        for index, child in enumerate(children):
            text = self.render(child)
            if (
                child.get_type() == "RawText"
                and text.endswith("\\")
                and index + 1 < len(children)
                and children[index + 1].get_type() == "LineBreak"
            ):
                # A backslash before the end of a line is a hard line break,
                # and it would pair with the backslash of a hard line break
                text += "\\"
            if line_start and child.get_type() == "RawText":
                # A continuation line loses its indentation, so a leading block
                # marker would start a list, heading, etc. instead of continuing
                text = _escape_block_start(text, bool(self._second_prefix))
            elif (
                line_start
                and child.get_type() == "InlineHTML"
                and _HTML_BLOCK_START_RE.match(text)
            ):
                # An HTML tag cannot be escaped, but four spaces of indentation
                # keep it from starting an HTML block that ends the paragraph
                text = self._second_prefix + "    " + text
            line_start = child.get_type() == "LineBreak"
            parts.append(text)
        return "".join(parts)

    def render_list(self, element: block.List) -> str:
        result = []
        # An indented code block after the list was outside it, so the content of
        # the items started past column 4: indent the markers, or the code would
        # continue the last item
        before_code_block, self._before_code_block = self._before_code_block, False
        if element.ordered:
            # Keep the delimiter: "1." and "1)" lists are different lists
            delimiter = element.bullet[-1]
            for num, child in enumerate(element.children, element.start):
                width = len(str(num)) + 2
                lead = " " * max(0, 5 - width) if before_code_block else ""
                with self.container(f"{lead}{num}{delimiter} ", lead + " " * width):
                    result.append(self.render(child))
                # The first item wrote the marker of the item holding this list
                self._prefix = self._second_prefix
        else:
            lead = "   " if before_code_block else ""
            for child in element.children:
                with self.container(f"{lead}{element.bullet} ", lead + "  "):
                    result.append(self.render(child))
                self._prefix = self._second_prefix
        sep = self._second_prefix.rstrip() + "\n" if not element.tight else ""
        return sep.join(result)

    def render_list_item(self, element: block.ListItem) -> str:
        if all(child.get_type() == "BlankLine" for child in element.children):
            # An empty item has nothing to carry its marker, so write it here
            marker = self._prefix.rstrip() + "\n"
            self._prefix = self._second_prefix
            return marker + self.render_children(element)
        return self.render_children(element)

    def render_quote(self, element: block.Quote) -> str:
        with self.container("> ", "> "):
            result = self.render_children(element).rstrip("\n")
        self._prefix = self._second_prefix
        return result + "\n"

    def render_fenced_code(self, element: block.FencedCode) -> str:
        extra = f" {element.extra}" if element.extra else ""
        info = f"{element.lang}{extra}"
        # The code as written: render_raw_text() would space CJK and latin letters
        code = element.children[0].children  # type: ignore
        marker = "~" if "`" in info else "`"
        fence = marker * max(
            3, max(map(len, re.findall(marker + "+", code)), default=0) + 1
        )
        if info.startswith(marker):
            info = " " + info
        lines = [self._prefix + fence + info]
        code_lines = code.removesuffix("\n").split("\n") if code else []
        lines.extend(self._second_prefix + line for line in code_lines)
        lines.append(self._second_prefix + fence)
        self._prefix = self._second_prefix
        return "\n".join(lines) + "\n"

    def render_code_block(self, element: block.CodeBlock) -> str:
        indent = " " * 4
        code = element.children[0].children  # type: ignore
        lines = code.removesuffix("\n").split("\n")
        lines = [self._prefix + indent + lines[0]] + [
            self._second_prefix + indent + line for line in lines[1:]
        ]
        self._prefix = self._second_prefix
        return "\n".join(lines) + "\n"

    def render_html_block(self, element: block.HTMLBlock) -> str:
        lines = element.body.removesuffix("\n").split("\n")
        lines = [self._prefix + lines[0]] + [
            (self._second_prefix + line) if line else self._second_prefix.rstrip()
            for line in lines[1:]
        ]
        self._prefix = self._second_prefix
        return "\n".join(lines) + "\n"

    def render_thematic_break(self, element: block.ThematicBreak) -> str:
        result = self._prefix + "* * *\n"
        self._prefix = self._second_prefix
        return result

    def render_heading(self, element: block.Heading) -> str:
        result = (
            self._prefix
            + "#" * element.level
            + " "
            + self.render_children(element)
            + "\n"
        )
        self._prefix = self._second_prefix
        return result

    def render_setext_heading(self, element: block.SetextHeading) -> str:
        children = self._render_paragraph_children(element)
        if "\n" not in children:
            return self.render_heading(cast("block.Heading", element))
        # An ATX heading holds one line only, so keep a multi-line heading setext
        lines = children.split("\n")
        underline = "===" if element.level == 1 else "---"
        result = (
            self._prefix
            + lines[0]
            + "\n"
            + "".join(self._second_prefix + line + "\n" for line in lines[1:])
            + self._second_prefix
            + underline
            + "\n"
        )
        self._prefix = self._second_prefix
        return result

    def render_blank_line(self, element: block.BlankLine) -> str:
        # Keep the quote markers, or the blank line would end the block quote. It is
        # the first line of an item that starts with an empty quote, so it has the
        # marker of the item
        line = self._prefix.rstrip() + "\n"
        self._prefix = self._second_prefix
        return line

    def render_link_ref_def(self, element: block.LinkRefDef) -> str:
        link_text = element.dest
        if element.title:
            link_text += f" {element.title}"
        result = f"{self._prefix}[{element.label}]: {link_text}\n"
        self._prefix = self._second_prefix
        return result

    def render_emphasis(self, element: inline.Emphasis) -> str:
        return self._render_emphasis(element, "*")

    def render_strong_emphasis(self, element: inline.StrongEmphasis) -> str:
        return self._render_emphasis(element, "*")

    def _render_emphasis(
        self, element: inline.Emphasis | inline.StrongEmphasis, char: str
    ) -> str:
        delimiter = char * (2 if element.get_type() == "StrongEmphasis" else 1)
        children = element.children
        if (
            len(children) == 1
            and not isinstance(children[0], str)
            and children[0].get_type() == "Emphasis"
        ):
            # `*` around it would join its `*` into one run of delimiters, so
            # `**_foo_**` would come back as `***foo***`, which is <em><strong>
            other = "_" if char == "*" else "*"
            inner = self._render_emphasis(cast("inline.Emphasis", children[0]), other)
            return delimiter + inner + delimiter
        # A `*` in the text was not a delimiter, but next to the `*` of the emphasis
        # it would be one, so `_*_` would come back as `***`
        inner = "".join(
            (
                self.render(child).replace("*", "\\*")
                if child.get_type() == "RawText"
                else self.render(child)
            )
            for child in children
        )
        return delimiter + inner + delimiter

    def render_inline_html(self, element: inline.InlineHTML) -> str:
        return cast(str, element.children)

    @staticmethod
    def _render_link_destination(dest: str) -> str:
        escaped = re.sub(r"([\\<>])", r"\\\1", dest)
        if not dest or re.search(r"\s|[()<>]", dest):
            return f"<{escaped}>"
        return escaped

    def render_link(self, element: inline.Link) -> str:
        link_text = self.render_children(element)
        link_title = (
            '"{}"'.format(element.title.replace('"', '\\"')) if element.title else None
        )
        assert self.root_node
        label = next(
            (
                k
                for k, v in self.root_node.link_ref_defs.items()
                if v == (element.dest, link_title)
            ),
            None,
        )
        if label is not None:
            if label == link_text:
                return f"[{label}]"
            return f"[{link_text}][{label}]"
        title = f" {link_title}" if link_title is not None else ""
        return f"[{link_text}]({self._render_link_destination(element.dest)}{title})"

    def render_auto_link(self, element: inline.AutoLink) -> str:
        # The text: the destination of an email address starts with "mailto:"
        return f"<{self.render_children(element)}>"

    def render_image(self, element: inline.Image) -> str:
        template = "![{}]({}{})"
        title = (
            ' "{}"'.format(element.title.replace('"', '\\"')) if element.title else ""
        )
        return template.format(
            self.render_children(element),
            self._render_link_destination(element.dest),
            title,
        )

    def render_literal(self, element: inline.Literal) -> str:
        return f"\\{element.children}"

    def render_raw_text(self, element: inline.RawText) -> str:
        from .ext.pangu import PANGU_RE

        return re.sub(PANGU_RE, " ", element.children)

    def render_line_break(self, element: inline.LineBreak) -> str:
        return "\n" if element.soft else "\\\n"

    def render_code_span(self, element: inline.CodeSpan) -> str:
        text = cast(str, element.children)
        delimiter = "`" * (
            max((len(m.group()) for m in re.finditer(r"`+", text)), default=0) + 1
        )
        if (
            text.startswith("`")
            or text.endswith("`")
            or (text.startswith(" ") and text.endswith(" ") and text.strip())
        ):
            text = f" {text} "
        return f"{delimiter}{text}{delimiter}"
