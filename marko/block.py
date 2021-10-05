"""
Block level elements
"""
import re
from . import inline, patterns
from .helpers import Source, is_paired, normalize_label, is_type_check
from .parser import Parser
from .element import Element

if is_type_check():
    from typing import Any, Optional, Match, Dict, Union, Tuple, List as _List

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
    priority = 5
    #: if True, it won't be included in parsing process but produced by other elements
    #: other elements instead.
    virtual = False
    #: Whether children are parsed as inline elements.
    inline_children = False
    #: If true, will replace the element which it derives from.
    override = False
    _prefix = ""

    @classmethod
    def match(self, source):  # type: (Source) -> Any
        """Test if the source matches the element at current position.
        The source should not be consumed in the method unless you have to.

        :param source: the ``Source`` object of the content to be parsed
        """
        raise NotImplementedError()

    @classmethod
    def parse(self, source):  # type: (Source) -> Any
        """Parses the source. This is a proper place to consume the source body and
        return an element or information to build one. The information tuple will be
        passed to ``__init__`` method afterwards. Inline parsing, if any, should also
        be performed here.

        :param source: the ``Source`` object of the content to be parsed
        """
        raise NotImplementedError()

    def parse_inline(self):  # type: () -> None
        """Inline parsing is postponed so that all link references
        are seen before that.
        """
        if self.inline_children:
            self.children = parser.parse_inline(self.children)  # type: ignore
        elif isinstance(getattr(self, "children", None), list):
            for child in self.children:
                if isinstance(child, BlockElement):
                    child.parse_inline()

    def __lt__(self, o):  # type: (BlockElement) -> bool
        return self.priority < o.priority


class Document(BlockElement):
    """Document node element."""

    _prefix = ""
    virtual = True

    def __init__(self, text):  # type: (str) -> None
        self.link_ref_defs = {}  # type: Dict[str, Tuple[str, str]]
        source = Source(text)
        inline._root_node = self  # type: ignore
        with source.under_state(self):
            self.children = parser.parse(source)  # type: ignore
        self.parse_inline()


class BlankLine(BlockElement):
    """Blank lines"""

    priority = 5

    def __init__(self, start):  # type: (int) -> None
        self._anchor = start

    @classmethod
    def match(cls, source):  # type: (Source) -> bool
        line = source.next_line()
        return line is not None and not line.strip()

    @classmethod
    def parse(cls, source):  # type: (Source) -> int
        start = source.pos
        while not source.exhausted and cls.match(source):
            source.consume()
        return start


class Heading(BlockElement):
    """Heading element: (### Hello\n)"""

    priority = 6
    pattern = re.compile(
        r" {0,3}(#{1,6})((?=\s)[^\n]*?|[^\n\S]*)(?:(?<=\s)(?<!\\)#+)?[^\n\S]*$\n?",
        flags=re.M,
    )
    inline_children = True

    def __init__(self, match):  # type: (Match) -> None
        self.level = len(match.group(1))
        self.children = match.group(2).strip()

    @classmethod
    def match(cls, source):  # type: (Source) -> Optional[Match]
        return source.expect_re(cls.pattern)

    @classmethod
    def parse(cls, source):  # type: (Source) -> Optional[Match]
        m = source.match
        source.consume()
        return m


class SetextHeading(BlockElement):
    """Setext heading: (Hello\n===\n)
    It can only be created by Paragraph.parse.
    """

    virtual = True
    inline_children = True

    def __init__(self, lines):  # type: (_List[str]) -> None
        self.level = 1 if lines.pop().strip()[0] == "=" else 2
        self.children = "".join(line.lstrip() for line in lines).strip()


class CodeBlock(BlockElement):
    """Indented code block: (    this is a code block\n)"""

    priority = 4

    def __init__(self, lines):  # type: (str) -> None
        self.children = [inline.RawText(lines, False)]
        self.lang = ""
        self.extra = ""

    @classmethod
    def match(cls, source):  # type: (Source) -> str
        line = source.next_line(False)
        prefix = source.prefix + " {4}"
        if isinstance(source.state, Quote):
            # requires five spaces to prefix
            prefix = source.prefix[:-1] + " {4}"
        return cls.strip_prefix(line, prefix)  # type: ignore

    @classmethod
    def parse(cls, source):  # type: (Source) -> str
        prefix = source.prefix + " {4}"
        lines = [cls.match(source)]
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
                lines.append(cls.match(source))
                source.consume()
                source.anchor()
            else:
                source.reset()
                break
        return "".join(lines).rstrip("\n") + "\n"

    @staticmethod
    def strip_prefix(line, prefix):  # type: (str, str) -> str
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

    priority = 7
    pattern = re.compile(r"( {,3})(`{3,}|~{3,})[^\n\S]*(.*?)$", re.M)
    _parse_info = ("", "", "", "")  # type: Tuple[str, str, str, str]

    def __init__(self, match):  # type: (Tuple[str, str, str]) -> None
        self.lang = inline.Literal.strip_backslash(match[0])
        self.extra = match[1]
        self.children = [inline.RawText(match[2], False)]

    @classmethod
    def match(cls, source):  # type: (Source) -> Optional[Match]
        m = source.expect_re(cls.pattern)
        if not m:
            return None
        prefix, leading, info = m.groups()
        if leading[0] == "`" and "`" in info:
            return None
        lang, extra = (info.split(None, 1) + [""] * 2)[:2]
        cls._parse_info = prefix, leading, lang, extra
        return m

    @classmethod
    def parse(cls, source):  # type: (Source) -> Tuple[str, str, str]
        source.next_line()
        source.consume()
        lines = []
        while not source.exhausted:
            line = source.next_line()
            if line is None:
                break
            source.consume()
            m = re.match(r" {,3}(~+|`+)[^\n\S]*$", line, flags=re.M)
            if m and cls._parse_info[1] in m.group(1):
                break

            prefix_len = source.match_prefix(cls._parse_info[0], line)
            if prefix_len >= 0:
                line = line[prefix_len:]
            else:
                line = line.lstrip()
            lines.append(line)
        return cls._parse_info[2], cls._parse_info[3], "".join(lines)


class ThematicBreak(BlockElement):
    """Horizontal rules: (----\n)"""

    priority = 8
    pattern = re.compile(r" {,3}([-_*][^\n\S]*){3,}$\n?", flags=re.M)

    @classmethod
    def match(cls, source):  # type: (Source) -> bool
        m = source.expect_re(cls.pattern)
        if not m:
            return False
        return len(set(re.sub(r"\s+", "", m.group()))) == 1

    @classmethod
    def parse(cls, source):  # type: (Source) -> ThematicBreak
        source.consume()
        return cls()


class HTMLBlock(BlockElement):
    """HTML blocks, parsed as it is"""

    priority = 5
    _end_cond = None  # Optional[Match]

    def __init__(self, lines):  # type: (str) -> None
        self.children = lines

    @classmethod
    def match(cls, source):  # type: (Source) -> Union[int, bool]
        if source.expect_re(r"(?i) {,3}<(script|pre|style|textarea)[>\s]"):
            cls._end_cond = re.compile(rf"(?i)</{source.match.group(1)}>")
            return 1
        if source.expect_re(r" {,3}<!--"):
            cls._end_cond = re.compile(r"-->")
            return 2
        if source.expect_re(r" {,3}<\?"):
            cls._end_cond = re.compile(r"\?>")
            return 3
        if source.expect_re(r" {,3}<!"):
            cls._end_cond = re.compile(r">")
            return 4
        if source.expect_re(r" {,3}<!\[CDATA\["):
            cls._end_cond = re.compile(r"\]\]>")
            return 5
        block_tag = r"(?:{})".format("|".join(patterns.tags))
        if source.expect_re(r"(?im) {,3}</?%s(?: +|/?>|$)" % block_tag):
            cls._end_cond = None
            return 6
        if source.expect_re(
            r"(?m) {,3}(<%(tag)s(?:%(attr)s)*[^\n\S]*/?>|</%(tag)s[^\n\S]*>)[^\n\S]*$"
            % {"tag": patterns.tag_name, "attr": patterns.attribute_no_lf}
        ):
            cls._end_cond = None
            return 7

        return False

    @classmethod
    def parse(cls, source):  # type: (Source) -> str
        lines = []
        while not source.exhausted:
            line = source.next_line()
            if line is None:
                break
            lines.append(line)
            if cls._end_cond is not None:
                if cls._end_cond.search(line):
                    source.consume()
                    break
            elif line.strip() == "":
                lines.pop()
                break
            source.consume()
        return "".join(lines)


class Paragraph(BlockElement):
    """A paragraph element"""

    priority = 1
    pattern = re.compile(r"[^\n]+$\n?", flags=re.M)
    inline_children = True

    def __init__(self, lines):  # type: (_List[str]) -> None
        str_lines = "".join(line.lstrip() for line in lines).rstrip("\n")
        self.children = str_lines
        self._tight = False

    @classmethod
    def match(cls, source):  # type: (Source) -> bool
        return source.expect_re(cls.pattern) is not None

    @staticmethod
    def is_setext_heading(line):  # type: (str) -> bool
        return re.match(r" {,3}(=+|-+)[^\n\S]*$", line) is not None

    @classmethod
    def break_paragraph(cls, source, lazy=False):  # type: (Source, bool) -> bool
        assert isinstance(parser, Parser)
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
            result = parser.block_elements["ListItem"].parse_leading(source.next_line())
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

    @classmethod
    def parse(cls, source):  # type: (Source) -> _List[str]
        lines = [source.next_line()]
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
                    return parser.block_elements["SetextHeading"](lines)  # type: ignore
            else:
                # check lazy continuation, store the previous state stack
                states = source._states[:]
                while len(source._states) > 1:
                    source.pop_state()
                    if source.next_line():
                        # matches the prefix, quit the loop
                        if cls.break_paragraph(source, True):
                            # stop the whole parsing
                            end_parse = True
                        else:
                            lines.append(source.next_line())
                            source.consume()
                        break
                source._states = states
        return lines  # type: ignore


class Quote(BlockElement):
    """block quote element: (> hello world)"""

    priority = 6
    _prefix = r" {,3}>[^\n\S]?"

    @classmethod
    def match(cls, source):  # type: (Source) -> Optional[Match]
        return source.expect_re(r" {,3}>")

    @classmethod
    def parse(cls, source):  # type: (Source) -> Quote
        state = cls()
        with source.under_state(state):
            state.children = parser.parse(source)  # type: ignore
        return state


class List(BlockElement):
    """List block element"""

    priority = 6
    _prefix = ""
    pattern = re.compile(r" {,3}(\d{1,9}[.)]|[*\-+])[ \t\n\r\f]")
    _parse_info = ("", False, 0)

    def __init__(self):  # type: () -> None
        self.bullet, self.ordered, self.start = self._parse_info
        self.start = int(self.start)
        self.tight = True

    @classmethod
    def match(cls, source):  # type: (Source) -> bool
        m = source.expect_re(cls.pattern)
        if not m:
            return False
        bullet, ordered, start = m.group(1), False, 1
        if bullet[:-1].isdigit():
            ordered = True
            start = bullet[:-1]
        cls._parse_info = (bullet, ordered, start)
        return m is not None

    @classmethod
    def parse(cls, source):  # type: (Source) -> List
        state = cls()
        children = []
        tight = True
        has_blank_line = False
        with source.under_state(state):
            while not source.exhausted:
                if parser.block_elements["ListItem"].match(source):  # type: ignore
                    el = parser.block_elements["ListItem"].parse(source)  # type: ignore
                    if not isinstance(el, BlockElement):
                        el = parser.block_elements["ListItem"](el)  # type: ignore
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

    _parse_info = (0, "", 0, "")
    virtual = True
    _tight = False
    pattern = re.compile(r" {,3}(\d{1,9}[.)]|[*\-+])[ \t\n\r\f]")

    def __init__(self):  # type: () -> None
        indent, bullet, mid, tail = self._parse_info
        self._prefix = " " * indent + re.escape(bullet) + " " * mid
        self._second_prefix = " " * (len(bullet) + indent + (mid or 1))

    @classmethod
    def parse_leading(cls, line):  # type: (str) -> Tuple[int, str, int, str]
        line = line.expandtabs(4)
        stripped_line = line.lstrip()
        indent = len(line) - len(stripped_line)
        temp = stripped_line.split(None, 1)
        bullet = temp[0]
        if len(temp) == 1:
            mid = 0
            tail = ""
        else:
            mid = len(stripped_line) - len("".join(temp))
            if mid > 4:
                mid = 1
            tail = temp[1]
        return indent, bullet, mid, tail

    @classmethod
    def match(cls, source):  # type: (Source) -> bool
        if parser.block_elements["ThematicBreak"].match(source):  # type: ignore
            return False
        if not source.expect_re(cls.pattern):
            return False
        next_line = source.next_line(False)
        assert next_line is not None
        prefix_pos = 0
        stripped_line = next_line
        for i in range(1, len(next_line) + 1):
            m = re.match(source.prefix, next_line[:i].expandtabs(4))
            if not m:
                continue
            if m.end() > prefix_pos:
                prefix_pos = m.end()
                stripped_line = next_line[:i].expandtabs(4)[prefix_pos:] + next_line[i:]
        indent, bullet, mid, tail = cls.parse_leading(stripped_line)  # type: ignore
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
        cls._parse_info = (indent, bullet, mid, tail)
        return True

    @classmethod
    def parse(cls, source):  # type: (Source) -> ListItem
        state = cls()
        state.children = []
        with source.under_state(state):
            if not source.next_line().strip():  # type: ignore
                source.consume()
                if not source.next_line() or not source.next_line().strip():  # type: ignore
                    return state
            state.children = parser.parse(source)  # type: ignore
        if isinstance(state.children[-1], BlankLine):
            # Remove the last blank line from list item
            blankline = state.children.pop()
            if state.children:
                source.pos = blankline._anchor
        return state


class LinkRefDef(BlockElement):
    """Link reference definition:
    [label]: destination "title"
    """

    pattern = re.compile(
        r" {,3}%s:(?P<s1>\s*)%s(?P<s2>\s*)(?:(?<=\s)%s)?[^\n\S]*$\n?"
        % (patterns.link_label, patterns.link_dest, patterns.link_title),
        flags=re.M,
    )
    _parse_info = ("", "", "")

    @classmethod
    def match(cls, source):  # type: (Source) -> bool
        m = source.expect_re(cls.pattern)
        if not m:
            return False
        rv = m.groupdict()
        if rv["s1"].count("\n") > 1 or rv["s1"].count("\n") > 1:
            return False
        label = rv["label"]
        if rv["dest"][0] == "<" and rv["dest"][-1] == ">":
            dest = rv["dest"]
        elif is_paired(rv["dest"], "(", ")"):
            dest = rv["dest"]
        else:
            return False
        title = rv["title"]
        if title and re.search(r"^$", title, re.M):
            return False
        cls._parse_info = label, dest, title
        return m is not None

    @classmethod
    def parse(cls, source):  # type: (Source) -> LinkRefDef
        label, dest, title = cls._parse_info
        normalized_label = normalize_label(label[1:-1])
        assert isinstance(source.root, Document)
        if normalized_label not in source.root.link_ref_defs:
            source.root.link_ref_defs[normalized_label] = (dest, title)
        source.consume()
        return cls()


parser = None
