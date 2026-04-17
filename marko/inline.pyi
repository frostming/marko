from typing import Iterator, Pattern, Sequence

from .element import Element
from .inline_parser import _Match
from .source import Source

__all__ = [
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
]

class InlineElement(Element):
    priority: int
    pattern: Pattern[str] | str
    parse_children: bool
    parse_group: int
    virtual: bool
    override: bool
    children: str | Sequence[Element]
    def __init__(self, match: _Match) -> None: ...
    @classmethod
    def find(cls, text: str, *, source: Source) -> Iterator[_Match]: ...

class Literal(InlineElement):
    priority: int
    pattern: Pattern[str]
    @classmethod
    def strip_backslash(cls, text: str) -> str: ...

class LineBreak(InlineElement):
    priority: int
    pattern: str
    soft: bool
    children: str
    def __init__(self, match: _Match) -> None: ...

class InlineHTML(InlineElement):
    priority: int
    pattern: Pattern[str]

class StrongEmphasis(InlineElement):
    virtual: bool
    parse_children: bool

class Emphasis(InlineElement):
    virtual: bool
    parse_children: bool

class Link(InlineElement):
    virtual: bool
    parse_children: bool
    dest: str
    title: str | None
    def __init__(self, match: _Match) -> None: ...

class Image(InlineElement):
    virtual: bool
    parse_children: bool
    dest: str
    title: str | None
    def __init__(self, match: _Match) -> None: ...

class CodeSpan(InlineElement):
    priority: int
    pattern: Pattern[str]
    children: str
    def __init__(self, match: _Match) -> None: ...

class AutoLink(InlineElement):
    priority: int
    pattern: Pattern[str]
    dest: str
    children: str
    title: str
    def __init__(self, match: _Match) -> None: ...

class RawText(InlineElement):
    virtual: bool
    children: str
    escape: bool
    def __init__(self, match: str, escape: bool = True) -> None: ...
