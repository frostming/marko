from typing import Any, Match, NamedTuple, Sequence

from . import inline_parser
from .element import Element
from .source import Source

__all__ = [
    "Document",
    "CodeBlock",
    "Heading",
    "List",
    "ListItem",
    "BlankLine",
    "Quote",
    "FencedCode",
    "ThematicBreak",
    "HTMLBlock",
    "LinkRefDef",
    "SetextHeading",
    "Paragraph",
]

class BlockElement(Element):
    children: Sequence[Element]
    priority: int
    virtual: bool
    inline_body: str
    override: bool
    @classmethod
    def match(cls, source: Source) -> Any: ...
    @classmethod
    def parse(cls, source: Source) -> Any: ...
    def __lt__(self, o: BlockElement) -> bool: ...

class Document(BlockElement):
    virtual: bool
    children: list[Element]
    link_ref_defs: dict[str, tuple[str, str]]
    def __init__(self) -> None: ...

class BlankLine(BlockElement):
    priority: int
    def __init__(self, start: int) -> None: ...
    @classmethod
    def match(cls, source: Source) -> bool: ...
    @classmethod
    def parse(cls, source: Source) -> int: ...

class Heading(BlockElement):
    priority: int
    pattern: Any
    level: int
    inline_body: str
    def __init__(self, match: Match[str]) -> None: ...
    @classmethod
    def match(cls, source: Source) -> Match[str] | None: ...
    @classmethod
    def parse(cls, source: Source) -> Match[str] | None: ...

class SetextHeading(BlockElement):
    virtual: bool
    level: int
    inline_body: str
    def __init__(self, lines: list[str]) -> None: ...

class CodeBlock(BlockElement):
    priority: int
    children: list[Element]
    lang: str
    extra: str
    def __init__(self, lines: str) -> None: ...
    @classmethod
    def match(cls, source: Source) -> str: ...
    @classmethod
    def parse(cls, source: Source) -> str: ...
    @staticmethod
    def strip_prefix(line: str, prefix: str) -> str: ...

class FencedCode(BlockElement):
    priority: int
    pattern: Any

    class ParseInfo(NamedTuple):
        prefix: str
        leading: str
        lang: str
        extra: str

    lang: str
    extra: str
    children: list[Element]
    def __init__(self, match: tuple[str, str, str]) -> None: ...
    @classmethod
    def match(cls, source: Source) -> Match[str] | None: ...
    @classmethod
    def parse(cls, source: Source) -> tuple[str, str, str]: ...

class ThematicBreak(BlockElement):
    priority: int
    pattern: Any
    @classmethod
    def match(cls, source: Source) -> bool: ...
    @classmethod
    def parse(cls, source: Source) -> ThematicBreak: ...

class HTMLBlock(BlockElement):
    priority: int
    body: str
    def __init__(self, lines: str) -> None: ...
    @classmethod
    def match(cls, source: Source) -> int | bool: ...
    @classmethod
    def parse(cls, source: Source) -> str: ...

class Paragraph(BlockElement):
    priority: int
    pattern: Any
    inline_body: str
    def __init__(self, lines: list[str]) -> None: ...
    @classmethod
    def match(cls, source: Source) -> bool: ...
    @staticmethod
    def is_setext_heading(line: str) -> bool: ...
    @classmethod
    def break_paragraph(cls, source: Source, lazy: bool = False) -> bool: ...
    @classmethod
    def parse(cls, source: Source) -> list[str] | SetextHeading: ...

class Quote(BlockElement):
    priority: int
    @classmethod
    def match(cls, source: Source) -> Match[str] | None: ...
    @classmethod
    def parse(cls, source: Source) -> Quote: ...

class List(BlockElement):
    priority: int
    pattern: Any

    class ParseInfo(NamedTuple):
        bullet: str
        ordered: bool
        start: int

    tight: bool
    ordered: bool
    start: int
    bullet: str
    def __init__(self, info: ParseInfo) -> None: ...
    @classmethod
    def match(cls, source: Source) -> bool: ...
    @classmethod
    def parse(cls, source: Source) -> List: ...

class ListItem(BlockElement):
    virtual: bool
    pattern: Any

    class ParseInfo(NamedTuple):
        indent: int
        bullet: str
        mid: int

    def __init__(self, info: ParseInfo) -> None: ...
    @classmethod
    def parse_leading(
        cls, line: str, prefix_pos: int
    ) -> tuple[int, str, int, str]: ...
    @classmethod
    def match(cls, source: Source) -> bool: ...
    @classmethod
    def parse(cls, source: Source) -> ListItem: ...

class LinkRefDef(BlockElement):
    pattern: Any

    class ParseInfo(NamedTuple):
        link_label: inline_parser.Group
        link_dest: inline_parser.Group
        link_title: inline_parser.Group
        end: int

    label: str
    dest: str
    title: str | None
    def __init__(self, label: str, text: str, title: str | None = None) -> None: ...
    @classmethod
    def match(cls, source: Source) -> bool: ...
    @classmethod
    def parse(cls, source: Source) -> LinkRefDef: ...
