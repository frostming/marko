"""
Block level elements
"""

from __future__ import annotations

import re
from typing import (
    TYPE_CHECKING,
    Any,
    Match,
    NamedTuple,
    cast,
    ClassVar,
    Optional,
)
from pydantic import Field

from . import inline, inline_parser, patterns
from .element import Element
from .helpers import find_next, normalize_label, partition_by_spaces

if TYPE_CHECKING:
    from .source import Source

__all__ = (
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
)


class BlockElement(Element):
    """Any block element should inherit this class"""

    #: Use to denote the precedence in parsing
    priority: ClassVar[int] = 5
    #: if True, it won't be included in parsing process but produced by other elements
    #: other elements instead.
    virtual: ClassVar[bool] = False
    #: If true, will replace the element which it derives from.
    override: ClassVar[bool] = False

    #: An attribute to hold the children
    children: list[Element] = Field(default_factory=list)
    #: If not empty, the body needs to be parsed as inline elements
    inline_body: str = ""
    _prefix: str = ""

    @classmethod
    def match(cls, source: Source) -> Any:
        """Test if the source matches the element at current position.
        The source should not be consumed in the method unless you have to.

        :param source: the ``Source`` object of the content to be parsed
        """
        raise NotImplementedError()

    @classmethod
    def parse(cls, source: Source) -> Any:
        """Parses the source. This is a proper place to consume the source body and
        return an element or information to build one. The information tuple will be
        passed to ``__init__`` method afterwards. Inline parsing, if any, should also
        be performed here.

        :param source: the ``Source`` object of the content to be parsed
        """
        raise NotImplementedError()

    def __lt__(self, o: BlockElement) -> bool:
        return self.priority < o.priority


class Document(BlockElement):
    """Document node element."""

    virtual: ClassVar[bool] = True

    link_ref_defs: dict[str, tuple[str, str]] = Field(default_factory=dict)


class BlankLine(BlockElement):
    """Blank lines"""

    priority: ClassVar[int] = 5

    anchor: int

    def __init__(self, start: int):
        super(BlockElement, self).__init__(**{"anchor": start})

    @classmethod
    def match(cls, source: Source) -> bool:
        line = source.next_line()
        return line is not None and not line.strip()

    @classmethod
    def parse(cls, source: Source) -> int:
        start = source.pos
        while not source.exhausted and cls.match(source):
            source.consume()
        return start


class Heading(BlockElement):
    """Heading element: (### Hello\n)"""

    priority: ClassVar[int] = 6
    pattern: ClassVar[re.Pattern] = re.compile(
        r" {0,3}(#{1,6})((?=\s)[^\n]*?|[^\n\S]*)(?:(?<=\s)(?<!\\)#+)?[^\n\S]*$\n?",
        flags=re.M,
    )

    level: int

    def __init__(self, match: Match[str]) -> None:
        super(BlockElement, self).__init__(
            **{"inline_body": match.group(2).strip(), "level": len(match.group(1))}
        )

    @classmethod
    def match(cls, source: Source) -> Match[str] | None:
        return source.expect_re(cls.pattern)

    @classmethod
    def parse(cls, source: Source) -> Match[str] | None:
        m = source.match
        source.consume()
        return m


class SetextHeading(BlockElement):
    """Setext heading: (Hello\n===\n)

    It can only be created by Paragraph.parse.
    """

    virtual: ClassVar[bool] = True

    level: int

    def __init__(self, lines: list[str]) -> None:
        _level = 1 if lines.pop().strip()[0] == "=" else 2
        super(BlockElement, self).__init__(
            **{
                "inline_body": "".join(line.lstrip() for line in lines).strip(),
                "level": _level,
            }
        )


class CodeBlock(BlockElement):
    """Indented code block: (    this is a code block\n)"""

    priority: ClassVar[int] = 4

    lang: str = ""
    extra: str = ""

    def __init__(self, lines: str) -> None:
        super(BlockElement, self).__init__(
            **{"children": [inline.RawText(lines, False)]}
        )

    @classmethod
    def match(cls, source: Source) -> str:
        line = source.next_line(False)
        prefix = source.prefix + " {4}"
        if isinstance(source.state, Quote):
            # requires five spaces to prefix
            prefix = source.prefix[:-1] + " {4}"
        line = cls.strip_prefix(line, prefix)
        source.context.code_line = line
        return line

    @classmethod
    def parse(cls, source: Source) -> str:
        prefix = source.prefix + " {4}"
        lines = [source.context.code_line]
        source.consume()
        source.anchor()
        while not source.exhausted:
            line = source.next_line()
            if line is not None and not line.strip():
                source.consume()
                stripped_line = cls.strip_prefix(line, prefix)
                if stripped_line:
                    lines.append(stripped_line)
                else:
                    lines.append("\n")
            elif cls.match(source):
                lines.append(source.context.code_line)
                source.consume()
                source.anchor()
            else:
                source.reset()
                break
        return "".join(lines).rstrip("\n") + "\n"

    @staticmethod
    def strip_prefix(line: str, prefix: str) -> str:
        match = re.match(prefix, line.expandtabs(4))
        if not match:
            return ""
        end = match.end()
        for i in range(len(line)):
            expanded = line[: i + 1].expandtabs(4)
            if len(expanded) < end:
                continue
            d = len(expanded) - end
            if d == 0:
                return line[i + 1 :]
            return expanded[-d:] + line[i + 1 :]
        return ""


class FencedCode(BlockElement):
    """Fenced code block: (```python\nhello\n```\n)"""

    priority: ClassVar[int] = 7
    pattern: ClassVar[re.Pattern] = re.compile(
        r"( {,3})(`{3,}|~{3,})[^\n\S]*(.*?)$", re.M
    )

    lang: str
    extra: str

    class ParseInfo(NamedTuple):
        prefix: str
        leading: str
        lang: str
        extra: str

    def __init__(self, match: tuple[str, str, str]) -> None:
        super(BlockElement, self).__init__(
            **{
                "children": [inline.RawText(match[2], False)],
                "lang": inline.Literal.strip_backslash(match[0]),
                "extra": match[1],
            }
        )

    @classmethod
    def match(cls, source: Source) -> Match[str] | None:
        m = source.expect_re(cls.pattern)
        if not m:
            return None
        prefix, leading, info = m.groups()
        if leading[0] == "`" and "`" in info:
            return None
        lang, _, extra = partition_by_spaces(info)
        source.context.code_info = cls.ParseInfo(prefix, leading, lang, extra)
        return m

    @classmethod
    def parse(cls, source: Source) -> tuple[str, str, str]:
        source.next_line()
        source.consume()
        lines = []
        parse_info: FencedCode.ParseInfo = source.context.code_info
        while not source.exhausted:
            line = source.next_line()
            if line is None:
                break
            source.consume()
            m = re.match(r" {,3}(~+|`+)[^\n\S]*$", line, flags=re.M)
            if m and parse_info.leading in m.group(1):
                break

            prefix_len = source.match_prefix(parse_info.prefix, line)
            if prefix_len >= 0:
                line = line[prefix_len:]
            else:
                line = line.lstrip()
            lines.append(line)
        return parse_info.lang, parse_info.extra, "".join(lines)


class ThematicBreak(BlockElement):
    """Horizontal rules: (----\n)"""

    priority: ClassVar[int] = 8
    pattern: ClassVar[re.Pattern] = re.compile(
        r" {,3}([-_*][^\n\S]*){3,}$\n?", flags=re.M
    )

    @classmethod
    def match(cls, source: Source) -> bool:
        m = source.expect_re(cls.pattern)
        if not m:
            return False
        return len(set(re.sub(r"\s+", "", m.group()))) == 1

    @classmethod
    def parse(cls, source: Source) -> ThematicBreak:
        source.consume()
        return cls()


class HTMLBlock(BlockElement):
    """HTML blocks, parsed as it is"""

    priority: ClassVar[int] = 5

    body: str

    def __init__(self, lines: str):
        super(BlockElement, self).__init__(**{"body": lines})

    @classmethod
    def match(cls, source: Source) -> int | bool:
        source.context.html_end = None
        if source.expect_re(r"(?i) {,3}<(script|pre|style|textarea)[>\s]"):
            assert source.match
            source.context.html_end = re.compile(rf"(?i)</{source.match.group(1)}>")
            return 1
        if source.expect_re(r" {,3}<!--"):
            source.context.html_end = re.compile(r"-->")
            return 2
        if source.expect_re(r" {,3}<\?"):
            source.context.html_end = re.compile(r"\?>")
            return 3
        if source.expect_re(r" {,3}<!"):
            source.context.html_end = re.compile(r">")
            return 4
        if source.expect_re(r" {,3}<!\[CDATA\["):
            source.context.html_end = re.compile(r"\]\]>")
            return 5
        block_tag = r"(?:{})".format("|".join(patterns.tags))
        if source.expect_re(r"(?im) {,3}</?%s(?: +|/?>|$)" % block_tag):
            source.context.html_end = None
            return 6
        if source.expect_re(
            r"(?m) {,3}(<%(tag)s(?:%(attr)s)*[^\n\S]*/?>|</%(tag)s[^\n\S]*>)[^\n\S]*$"
            % {"tag": patterns.tag_name, "attr": patterns.attribute_no_lf}
        ):
            source.context.html_end = None
            return 7

        return False

    @classmethod
    def parse(cls, source: Source) -> str:
        lines = []
        while not source.exhausted:
            line = source.next_line()
            if line is None:
                break
            lines.append(line)
            if source.context.html_end is not None:
                if source.context.html_end.search(line):
                    source.consume()
                    break
            elif line.strip() == "":
                lines.pop()
                break
            source.consume()
        return "".join(lines)


class Paragraph(BlockElement):
    """A paragraph element"""

    priority: ClassVar[int] = 1
    pattern: ClassVar[re.Pattern] = re.compile(r"[^\n]+$\n?", flags=re.M)

    _tight: bool = False

    def __init__(self, lines: list[str]) -> None:
        super(BlockElement, self).__init__(
            **{"inline_body": "".join(line.lstrip() for line in lines).rstrip("\n")}
        )

    @classmethod
    def match(cls, source: Source) -> bool:
        return source.expect_re(cls.pattern) is not None

    @staticmethod
    def is_setext_heading(line: str) -> bool:
        return re.match(r" {,3}(=+|-+)[^\n\S]*$", line) is not None

    @classmethod
    def break_paragraph(cls, source: Source, lazy: bool = False) -> bool:
        parser = source.parser
        prev_match = source.match
        try:
            if (
                parser.block_elements["Quote"].match(source)
                or parser.block_elements["Heading"].match(source)
                or parser.block_elements["BlankLine"].match(source)
                or parser.block_elements["FencedCode"].match(source)
            ):
                return True
            if (
                lazy
                and isinstance(source.state, List)
                and parser.block_elements["ListItem"].match(source)
            ):
                return True
            if parser.block_elements["List"].match(source):
                result = cast(
                    "type[ListItem]", parser.block_elements["ListItem"]
                ).parse_leading(source.next_line().rstrip(), 0)
                if lazy or (result[1][:-1] == "1" or result[1] in "*-+") and result[3]:
                    return True
            html_type = parser.block_elements["HTMLBlock"].match(source)
            if html_type and html_type != 7:
                return True
            if parser.block_elements["ThematicBreak"].match(source):
                if not lazy and cls.is_setext_heading(source.next_line()):
                    return False
                return True
            return False
        finally:
            source.match = prev_match

    @classmethod
    def parse(cls, source: Source) -> list[str] | SetextHeading:
        lines = [cast(str, source.next_line())]
        source.consume()
        end_parse = False
        while not source.exhausted and not end_parse:
            if cls.break_paragraph(source):
                break
            line = source.next_line()
            # the prefix is matched and not breakers
            if line:
                lines.append(line)
                source.consume()
                if cls.is_setext_heading(line):
                    return cast(
                        "type[SetextHeading]",
                        source.parser.block_elements["SetextHeading"],
                    )(lines)
            else:
                # check lazy continuation, store the previous state stack
                states = source._states[:]
                while len(source._states) > 1:
                    source.pop_state()
                    next_line = source.next_line()
                    if next_line:
                        # matches the prefix, quit the loop
                        if cls.break_paragraph(source, True):
                            # stop the whole parsing
                            end_parse = True
                        else:
                            lines.append(next_line)
                            source.consume()
                        break
                source._states = states
        return lines


class Quote(BlockElement):
    """block quote element: (> hello world)"""

    priority: ClassVar[int] = 6
    _prefix: str = r" {,3}>[^\n\S]?"

    @classmethod
    def match(cls, source: Source) -> Match[str] | None:
        return source.expect_re(r" {,3}>")

    @classmethod
    def parse(cls, source: Source) -> Quote:
        state = cls()
        with source.under_state(state):
            state.children = source.parser.parse_source(source)
        return state


class List(BlockElement):
    """List block element"""

    priority: ClassVar[int] = 6
    pattern: ClassVar[re.Pattern] = re.compile(r" {,3}(\d{1,9}[.)]|[*\-+])[ \t\n\r\f]")

    bullet: str
    ordered: bool
    start: int
    tight: bool = True

    class ParseInfo(NamedTuple):
        bullet: str
        ordered: bool
        start: int

    def __init__(self, info: List.ParseInfo) -> None:
        super(BlockElement, self).__init__(
            **{"bullet": info[0], "ordered": info[1], "start": info[2]}
        )

    @classmethod
    def match(cls, source: Source) -> bool:
        m = source.expect_re(cls.pattern)
        if not m:
            return False
        bullet, ordered, start = m.group(1), False, 1
        if bullet[:-1].isdigit():
            ordered = True
            start = int(bullet[:-1])
        source.context.list_info = cls.ParseInfo(bullet, ordered, start)
        return m is not None

    @classmethod
    def parse(cls, source: Source) -> List:
        state = cls(source.context.list_info)
        children = []
        tight = True
        has_blank_line = False
        parser = source.parser
        with source.under_state(state):
            while not source.exhausted:
                if parser.block_elements["ListItem"].match(source):
                    el = parser.block_elements["ListItem"].parse(source)
                    if not isinstance(el, BlockElement):
                        el = cast("type[ListItem]", parser.block_elements["ListItem"])(
                            el
                        )
                    children.append(el)
                    source.anchor()
                    if has_blank_line:
                        tight = False
                elif BlankLine.match(source):
                    BlankLine.parse(source)
                    has_blank_line = True
                else:
                    source.reset()
                    break
        tight = tight and not any(
            isinstance(e, BlankLine) for item in children for e in item.children
        )
        if tight:
            for item in children:
                item._tight = tight
                for child in item.children:
                    if isinstance(child, Paragraph):
                        child._tight = tight
        state.children = children
        state.tight = tight
        return state


class ListItem(BlockElement):
    """List item element. It can only be created by List.parse"""

    virtual: ClassVar[bool] = True
    pattern: ClassVar[re.Pattern] = re.compile(r" {,3}(\d{1,9}[.)]|[*\-+])[ \t\n\r\f]")

    _tight: bool = False

    indent: int
    bullet: str
    mid: int

    _second_prefix: str

    class ParseInfo(NamedTuple):
        indent: int
        bullet: str
        mid: int

    def __init__(self, info: ListItem.ParseInfo) -> None:
        _indent, _bullet, _mid = info
        super(BlockElement, self).__init__(
            **{
                "indent": _indent,
                "bullet": _bullet,
                "mid": _mid,
            }
        )
        self._prefix = " " * _indent + re.escape(_bullet) + " " * _mid
        self._second_prefix = " " * (len(_bullet) + _indent + (_mid or 1))

    @classmethod
    def parse_leading(cls, line: str, prefix_pos: int) -> tuple[int, str, int, str]:
        stripped_line = line[prefix_pos:].expandtabs(4).lstrip()
        indent = len(line) - prefix_pos - len(stripped_line)
        bullet, spaces, tail = partition_by_spaces(stripped_line)
        mid = len(spaces)
        if mid > 4:
            mid = 1
        return indent, bullet, mid, tail

    @classmethod
    def match(cls, source: Source) -> bool:
        if source.parser.block_elements["ThematicBreak"].match(source):
            return False
        if not source.expect_re(cls.pattern):
            return False
        next_line = cast(str, source.next_line(False)).expandtabs(4)
        prefix_pos = 0
        m = re.match(source.prefix, next_line)
        if m is not None:
            prefix_pos = m.end()
        indent, bullet, mid, _ = cls.parse_leading(next_line.rstrip(), prefix_pos)
        parent = source.state
        assert isinstance(parent, List)
        if (
            parent.ordered
            and not bullet[:-1].isdigit()
            or bullet[-1] != parent.bullet[-1]
        ):
            return False
        if not parent.ordered and bullet != parent.bullet:
            return False
        source.context.list_item_info = cls.ParseInfo(indent, bullet, mid)
        return True

    @classmethod
    def parse(cls, source: Source) -> ListItem:
        state = cls(source.context.list_item_info)
        state.children = []
        with source.under_state(state):
            if not source.next_line().strip():  # type: ignore[union-attr]
                source.consume()
                if not source.next_line() or not source.next_line().strip():  # type: ignore[union-attr]
                    return state
            state.children = source.parser.parse_source(source)
        if isinstance(state.children[-1], BlankLine):
            # Remove the last blank line from list item
            blankline = cast(BlankLine, state.children.pop())
            if state.children:
                source.pos = blankline.anchor
        return state


class LinkRefDef(BlockElement):
    """Link reference definition:
    [label]: destination "title"
    """

    pattern: ClassVar[re.Pattern] = re.compile(
        r" {,3}(\[[\s\S]*?)(?=\n\n|\Z)", flags=re.M
    )

    class ParseInfo(NamedTuple):
        link_label: inline_parser.Group
        link_dest: inline_parser.Group
        link_title: inline_parser.Group
        end: int

    label: str
    dest: str
    title: Optional[str]

    def __init__(self, label: str, text: str, title: str | None = None) -> None:
        super(BlockElement, self).__init__(
            **{"label": label, "dest": text, "title": title}
        )

    @classmethod
    def match(cls, source: Source) -> bool:
        m = source.expect_re(cls.pattern)
        if not m:
            return False
        text = source._buffer
        link_label = inline_parser._parse_link_label(text, m.start(1))
        if not link_label:  # no ending bracket
            return False
        if link_label.end >= len(text) or text[link_label.end] != ":":
            # no colon after the ending bracket
            return False
        i = inline_parser._parse_link_separator(text, link_label.end + 1)
        try:
            link_dest, link_title = inline_parser._parse_link_dest_title(text, i)
        except inline_parser.ParseError:
            return False
        i = max(link_dest.end, link_title.end)
        end = find_next(text, "\n", i)
        if end >= 0:
            end += 1
        else:
            end = len(text)
        if text[i:end].strip():
            if link_title.text and "\n" in text[link_dest.end : link_title.start]:
                link_title = inline_parser._EMPTY_GROUP
                end = find_next(text, "\n", link_dest.end) + 1
            else:
                # There is content after the link title
                return False
        source.context.linkref_info = cls.ParseInfo(
            link_label, link_dest, link_title, end
        )
        return True

    @classmethod
    def parse(cls, source: Source) -> LinkRefDef:
        label, dest, title, pos = source.context.linkref_info
        normalized_label = normalize_label(label.text[1:-1])
        link_ref_defs = source.root.link_ref_defs
        if normalized_label not in link_ref_defs:
            link_ref_defs[normalized_label] = (dest.text, title.text)
        source.pos = pos
        return cls(normalized_label, dest.text, title.text)
