"""
Inline(span) level elements
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from re import Pattern
from typing import TYPE_CHECKING

from . import patterns
from .element import Element, _translate_span

if TYPE_CHECKING:
    from .inline_parser import _Match
    from .source import Source

__all__ = (
    "AutoLink",
    "CodeSpan",
    "Emphasis",
    "Image",
    "InlineHTML",
    "LineBreak",
    "Link",
    "Literal",
    "RawText",
    "StrongEmphasis",
)


class InlineElement(Element):
    """Any inline element should inherit this class"""

    #: Use to denote the precedence in parsing.
    priority = 5
    #: element regex pattern.
    pattern: Pattern[str] | str = ""
    #: whether to parse children.
    parse_children = False
    #: which match group to parse.
    parse_group = 1
    #: if True, it won't be included in parsing process but produced by
    #: other elements instead.
    virtual = False
    #: If true, will replace the element which it derives from.
    override = False

    if TYPE_CHECKING:
        children: str | Sequence[Element]

    def __init__(self, match: _Match) -> None:
        """Parses the matched object into an element"""
        if not self.parse_children:
            self.children = match.group(self.parse_group)

    @classmethod
    def find(cls, text: str, *, source: Source) -> Iterator[_Match]:
        """This method should return an iterable containing matches of this element."""
        if isinstance(cls.pattern, str):
            cls.pattern = re.compile(cls.pattern)
        return cls.pattern.finditer(text)

    def _syntax_spans(self, match: _Match) -> list[tuple[int, int]] | None:
        """Return the spans of the syntax characters (e.g. ``**`` of emphasis,
        brackets of a link) in the match, relative to the parsed text, or
        ``None`` if the element has no syntax characters to report.
        Subclasses may override this method.

        By default, the leading and trailing parts of the match that are not
        in the ``parse_group`` are considered syntax.
        """
        if self.parse_children:
            return [
                (match.start(), match.start(self.parse_group)),
                (match.end(self.parse_group), match.end()),
            ]
        return None

    def _set_extra_source_spans(
        self, match: _Match, positions: Sequence[int] | None
    ) -> None:
        """A hook to set additional source position attributes (e.g. the
        destination span of a link) on the element. Called by the inline
        parser when source positions are available.
        """


class Literal(InlineElement):
    """Literal escapes need to be parsed at the first."""

    priority = 7
    pattern = re.compile(r'\\([!"#\$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~])')

    @classmethod
    def strip_backslash(cls, text: str) -> str:
        return cls.pattern.sub(r"\1", text)

    def _syntax_spans(self, match: _Match) -> list[tuple[int, int]]:
        # The backslash.
        return [(match.start(), match.start(1))]


class LineBreak(InlineElement):
    """Line breaks:

    Soft: '\n'
    Hard: '  \n'
    """

    priority = 2
    pattern = r"( *|\\)\n(?!\Z)"

    def __init__(self, match: _Match) -> None:
        self.soft = not match.group(1).startswith(("  ", "\\"))
        self.children = "\n"

    def _syntax_spans(self, match: _Match) -> list[tuple[int, int]]:
        # Trailing spaces or the backslash that makes a hard line break.
        return [(match.start(), match.end(1))]

    @classmethod
    def find(cls, text: str, *, source: Source) -> Iterator[_Match]:
        """This method should return an iterable containing matches of this element."""
        # HACK: short circuit to avoid quadratic runtime when text doesn't have a linebreak.
        # ideally the regex pattern should be rewritten, but this works for now.
        # see issue #219
        if "\n" not in text:
            return iter(())
        return super().find(text, source=source)


class InlineHTML(InlineElement):
    priority = 7
    pattern = re.compile(
        r"(<%s(?:%s)* */?>"  # open tag
        r"|</%s *>"  # closing tag
        r"|<!--(?:>|->|[\s\S]*?-->)"  # HTML comment
        r"|<\?[\s\S]*?\?>"  # processing instruction
        r"|<![A-Z]+ +[\s\S]*?>"  # declaration
        r"|<!\[CDATA\[[\s\S]*?\]\]>)"  # CDATA section
        % (patterns.tag_name, patterns.attribute, patterns.tag_name)
    )


class StrongEmphasis(InlineElement):
    """Strong emphasis: **sample text**"""

    virtual = True
    parse_children = True


class Emphasis(InlineElement):
    """Emphasis: *sample text*"""

    virtual = True
    parse_children = True


class Link(InlineElement):
    """Link: [text](/link/destination)"""

    virtual = True
    parse_children = True

    def __init__(self, match: _Match) -> None:
        if match.group(2) and match.group(2)[0] == "<" and match.group(2)[-1] == ">":
            self.dest = match.group(2)[1:-1]
        else:
            self.dest = match.group(2) or ""
        self.dest = Literal.strip_backslash(self.dest)
        self.title = (
            Literal.strip_backslash(match.group(3)[1:-1]) if match.group(3) else None
        )
        self.dest_span: tuple[int, int] | None = None
        self.title_span: tuple[int, int] | None = None

    def _set_extra_source_spans(
        self, match: _Match, positions: Sequence[int] | None
    ) -> None:
        self.dest_span = _translate_span(positions, match.start(2), match.end(2))
        self.title_span = _translate_span(positions, match.start(3), match.end(3))


class Image(InlineElement):
    """Image: ![alt](/src/address)"""

    virtual = True
    parse_children = True

    def __init__(self, match: _Match) -> None:
        if match.group(2) and match.group(2)[0] == "<" and match.group(2)[-1] == ">":
            self.dest = match.group(2)[1:-1]
        else:
            self.dest = match.group(2) or ""
        self.dest = Literal.strip_backslash(self.dest)
        self.title = (
            Literal.strip_backslash(match.group(3)[1:-1]) if match.group(3) else None
        )
        self.dest_span: tuple[int, int] | None = None
        self.title_span: tuple[int, int] | None = None

    def _set_extra_source_spans(
        self, match: _Match, positions: Sequence[int] | None
    ) -> None:
        self.dest_span = _translate_span(positions, match.start(2), match.end(2))
        self.title_span = _translate_span(positions, match.start(3), match.end(3))


class CodeSpan(InlineElement):
    """Inline code span: `code sample`"""

    priority = 7
    pattern = re.compile(r"(?<!`)(`+)(?!`)([\s\S]+?)(?<!`)\1(?!`)")

    def __init__(self, match: _Match) -> None:
        self.children = match.group(2).replace("\n", " ")
        if self.children.strip() and self.children[0] == self.children[-1] == " ":
            self.children = self.children[1:-1]

    def _syntax_spans(self, match: _Match) -> list[tuple[int, int]]:
        # The backticks on both sides.
        return [
            (match.start(), match.start(2)),
            (match.end(2), match.end()),
        ]


class AutoLink(InlineElement):
    """Autolinks: <http://example.org>"""

    priority = 7
    pattern = re.compile(rf"<({patterns.uri}|{patterns.email})>")

    def __init__(self, match: _Match) -> None:
        self.dest = match.group(1)
        if re.match(patterns.email, self.dest):
            self.dest = "mailto:" + self.dest
        self.children = [RawText(match.group(1))]
        self.title = ""

    def _syntax_spans(self, match: _Match) -> list[tuple[int, int]]:
        # The angle brackets.
        return [
            (match.start(), match.start() + 1),
            (match.end() - 1, match.end()),
        ]

    def _set_extra_source_spans(
        self, match: _Match, positions: Sequence[int] | None
    ) -> None:
        child = self.children[0]
        if isinstance(child, Element):
            child.source_span = _translate_span(positions, match.start(1), match.end(1))


class RawText(InlineElement):
    """The raw text is the fallback for all holes that doesn't match any others."""

    virtual = True
    if TYPE_CHECKING:
        children: str

    def __init__(self, match: str, escape: bool = True) -> None:
        self.children = match
        self.escape = escape
