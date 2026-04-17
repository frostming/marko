from typing import Any, NamedTuple, Pattern

from . import patterns as patterns
from .helpers import find_next as find_next
from .helpers import is_paired as is_paired
from .helpers import normalize_label as normalize_label
from .inline import InlineElement
from .source import Source

ElementType = type[InlineElement]

# Type alias for match objects used in inline parsing
_Match = Any  # Can be re.Match[str] or MatchObj

class Group(NamedTuple):
    start: int
    end: int
    text: str | None

WHITESPACE: str
ASCII_CONTROL: Pattern[str]

class ParseError(ValueError): ...

def parse(
    text: str, elements: list[ElementType], fallback: ElementType, source: Source
) -> list[InlineElement]: ...
def make_elements(
    tokens: list[Token],
    text: str,
    start: int = 0,
    end: int | None = None,
    fallback: ElementType | None = None,
) -> list[InlineElement]: ...

class Token:
    PRECEDE: int
    INTERSECT: int
    CONTAIN: int
    SHADE: int
    etype: ElementType
    match: _Match
    start: int
    end: int
    inner_start: int
    inner_end: int
    text: str
    fallback: ElementType
    children: list[Token]
    def __init__(
        self, etype: ElementType, match: _Match, text: str, fallback: ElementType
    ) -> None: ...
    def relation(self, other: Token) -> int: ...
    def append_child(self, child: Token) -> None: ...
    def as_element(self) -> InlineElement: ...
    def __lt__(self, o: Token) -> bool: ...

def find_links_or_emphs(
    text: str, link_ref_defs: dict[str, tuple[str, str]]
) -> list[MatchObj]: ...
def look_for_image_or_link(
    text: str,
    delimiters: list[Delimiter],
    close: int,
    link_ref_defs: dict[str, tuple[str, str]],
    matches: list[MatchObj],
) -> MatchObj | None: ...
def process_emphasis(
    text: str,
    delimiters: list[Delimiter],
    stack_bottom: int | None,
    matches: list[MatchObj],
) -> None: ...

class Delimiter:
    whitespace_re: Pattern[str]
    start: int
    end: int
    content: str
    text: str
    active: bool
    can_open: bool
    can_close: bool
    def __init__(self, match: _Match, text: str) -> None: ...
    def is_left_flanking(self) -> bool: ...
    def is_right_flanking(self) -> bool: ...
    def followed_by_punc(self) -> bool: ...
    def preceded_by_punc(self) -> bool: ...
    def closed_by(self, other: Delimiter) -> bool: ...
    def remove(self, n: int, left: bool = False) -> bool: ...

class MatchObj:
    etype: str
    def __init__(
        self, etype: str, text: str, start: int, end: int, *groups: Group
    ) -> None: ...
    def group(self, n: int = 0) -> str: ...
    def start(self, n: int = 0) -> int: ...
    def end(self, n: int = 0) -> int: ...
    def span(self, n: int = 0) -> tuple[int, int]: ...
