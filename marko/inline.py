"""
Inline(span) level elements
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Iterator, Pattern, Sequence, ClassVar, Optional, Any
from pydantic import Field

from . import patterns
from .element import Element

if TYPE_CHECKING:
    from .inline_parser import _Match
    from .source import Source

__all__ = (
    "LineBreak",
    "Literal",
    "InlineHTML",
    "CodeSpan",
    "Emphasis",
    "StrongEmphasis",
    "Link",
    "Image",
    "AutoLink",
    "RawText",
)


class InlineElement(Element):
    """Any inline element should inherit this class"""

    #: Use to denote the precedence in parsing.
    priority: ClassVar[int] = 5
    #: element regex pattern.
    pattern: ClassVar[re.Pattern | str] = ""
    #: whether to parse children.
    parse_children: ClassVar[bool] = False
    #: which match group to parse.
    parse_group: ClassVar[int] = 1
    #: if True, it won't be included in parsing process but produced by
    #: other elements instead.
    virtual: ClassVar[bool] = False
    #: If true, will replace the element which it derives from.
    override: ClassVar[bool] = False

    children: Optional[str | Sequence[Element]] = None

    @classmethod
    def initialize_kwargs(cls, match: _Match) -> dict[str, Any]:
        """Parses the matched object into an element"""
        return {} if cls.parse_children else {"children": match.group(cls.parse_group)}

    @classmethod
    def find(cls, text: str, *, source: Source) -> Iterator[_Match]:
        """This method should return an iterable containing matches of this element."""
        if isinstance(cls.pattern, str):
            cls.pattern = re.compile(cls.pattern)
        return cls.pattern.finditer(text)


class Literal(InlineElement):
    """Literal escapes need to be parsed at the first."""

    priority: ClassVar[int] = 7
    pattern: ClassVar[re.Pattern | str] = re.compile(
        r'\\([!"#\$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~])'
    )

    @classmethod
    def strip_backslash(cls, text: str) -> str:
        return cls.pattern.sub(r"\1", text)  # type: ignore[unio]


class LineBreak(InlineElement):
    """Line breaks:

    Soft: '\n'
    Hard: '  \n'
    """

    priority: ClassVar[int] = 2
    pattern: ClassVar[re.Pattern | str] = r"( *|\\)\n(?!\Z)"

    soft: bool

    @classmethod
    def initialize_kwargs(cls, match: _Match) -> dict[str, Any]:
        return {
            "soft": not match.group(1).startswith(("  ", "\\")),
            "children": "\n",
        }


class InlineHTML(InlineElement):
    priority: ClassVar[int] = 7
    pattern: ClassVar[re.Pattern | str] = re.compile(
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

    virtual: ClassVar[bool] = True
    parse_children: ClassVar[bool] = True


class Emphasis(InlineElement):
    """Emphasis: *sample text*"""

    virtual: ClassVar[bool] = True
    parse_children: ClassVar[bool] = True


class Link(InlineElement):
    """Link: [text](/link/destination)"""

    virtual: ClassVar[bool] = True
    parse_children: ClassVar[bool] = True

    dest: str
    title: Optional[str]

    @classmethod
    def initialize_kwargs(cls, match: _Match) -> dict[str, Any]:
        if match.group(2) and match.group(2)[0] == "<" and match.group(2)[-1] == ">":
            _dest = match.group(2)[1:-1]
        else:
            _dest = match.group(2) or ""
        return {
            "dest": Literal.strip_backslash(_dest),
            "title": (
                Literal.strip_backslash(match.group(3)[1:-1])
                if match.group(3)
                else None
            ),
        }


class Image(InlineElement):
    """Image: ![alt](/src/address)"""

    virtual: ClassVar[bool] = True
    parse_children: ClassVar[bool] = True

    dest: str
    title: Optional[str]

    @classmethod
    def initialize_kwargs(cls, match: _Match) -> dict[str, Any]:
        if match.group(2) and match.group(2)[0] == "<" and match.group(2)[-1] == ">":
            _dest = match.group(2)[1:-1]
        else:
            _dest = match.group(2) or ""
        return {
            "dest": Literal.strip_backslash(_dest),
            "title": (
                Literal.strip_backslash(match.group(3)[1:-1])
                if match.group(3)
                else None
            ),
        }


class CodeSpan(InlineElement):
    """Inline code span: `code sample`"""

    priority: ClassVar[int] = 7
    pattern: ClassVar[re.Pattern | str] = re.compile(
        r"(?<!`)(`+)(?!`)([\s\S]+?)(?<!`)\1(?!`)"
    )

    @classmethod
    def initialize_kwargs(cls, match: _Match) -> dict[str, Any]:
        _children = match.group(2).replace("\n", " ")
        if _children.strip() and _children[0] == _children[-1] == " ":
            _children = _children[1:-1]
        return {
            "children": _children,
        }


class AutoLink(InlineElement):
    """Autolinks: <http://example.org>"""

    priority: ClassVar[int] = 7
    pattern: ClassVar[re.Pattern | str] = re.compile(
        rf"<({patterns.uri}|{patterns.email})>"
    )

    dest: str
    title: Optional[str]

    @classmethod
    def initialize_kwargs(cls, match: _Match) -> dict[str, Any]:
        _dest = match.group(1)
        if re.match(patterns.email, _dest):
            _dest = "mailto:" + _dest
        return {
            "children": [RawText.initialize(match.group(1))],
            "title": "",
            "dest": _dest,
        }


class RawText(InlineElement):
    """The raw text is the fallback for all holes that doesn't match any others."""

    virtual: ClassVar[bool] = True

    escape: bool

    @classmethod
    def initialize_kwargs(cls, match: str, escape: bool = True) -> dict[str, Any]:  # type: ignore[override]
        return {
            "children": match,
            "escape": escape,
        }
