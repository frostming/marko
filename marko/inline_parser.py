"""
Parse inline elements
"""
import re
import string

from .helpers import is_paired, normalize_label, is_type_check
from . import patterns

if is_type_check():
    from typing import Type, List, Optional, Match, Tuple, Union
    from .inline import InlineElement
    from .block import Document

    ElementType = Type[InlineElement]
    Group = Tuple[int, int, Optional[str]]


def parse(text, elements, fallback):
    # type: (str, List[ElementType], ElementType) -> List[InlineElement]
    """Parse given text and produce a list of inline elements.

    :param text: the text to be parsed.
    :param elements: the element types to be included in parsing
    :param fallback: fallback class when no other element type is matched.
    """
    # this is a raw list of elements that may contain overlaps.
    tokens = []  # type: List[Token]
    for etype in elements:
        for match in etype.find(text):
            tokens.append(Token(etype, match, text, fallback))
    tokens.sort()
    tokens = _resolve_overlap(tokens)
    return make_elements(tokens, text, fallback=fallback)


def _resolve_overlap(tokens):
    # type: (List[Token]) -> List[Token]
    if not tokens:
        return tokens
    result = []
    prev = tokens[0]
    for cur in tokens[1:]:
        r = prev.relation(cur)
        if r == Token.PRECEDE:
            result.append(prev)
            prev = cur
        elif r == Token.CONTAIN:
            prev.append_child(cur)
        elif r == Token.INTERSECT and prev.etype.priority < cur.etype.priority:
            prev = cur
    result.append(prev)
    return result


def make_elements(tokens, text, start=0, end=None, fallback=None):
    # type: (List[Token], str, int, Optional[int], ElementType) -> List[InlineElement]
    """Make elements from a list of parsed tokens.
    It will turn all unmatched holes into fallback elements.

    :param tokens: a list of parsed tokens.
    :param text: the original tet.
    :param start: the offset of where parsing starts. Defaults to the start of text.
    :param end: the offset of where parsing ends. Defauls to the end of text.
    :param fallback: fallback element type.
    :returns: a list of inline elements.
    """
    result = []  # type: List[InlineElement]
    end = end or len(text)
    prev_end = start
    for token in tokens:
        if prev_end < token.start:
            result.append(fallback(text[prev_end : token.start]))  # type: ignore
        result.append(token.as_element())
        prev_end = token.end
    if prev_end < end:
        result.append(fallback(text[prev_end:end]))  # type: ignore
    return result


class Token:
    """An intermediate class to wrap the match object.
    It can be converted to element by :meth:`as_element()`
    """

    PRECEDE = 0
    INTERSECT = 1
    CONTAIN = 2
    SHADE = 3

    def __init__(self, etype, match, text, fallback):
        # type: (ElementType, _Match, str, ElementType) -> None
        self.etype = etype
        self.match = match
        self.start = match.start()
        self.end = match.end()
        self.inner_start = match.start(etype.parse_group)
        self.inner_end = match.end(etype.parse_group)
        self.text = text
        self.fallback = fallback
        self.children = []  # type: List[Token]

    def relation(self, other):  # type: (Token) -> int
        if self.end <= other.start:
            return Token.PRECEDE
        if self.end >= other.end:
            if (
                self.etype.parse_children
                and other.start >= self.inner_start
                and other.end <= self.inner_end
            ):
                return Token.CONTAIN
            if self.etype.parse_children and self.inner_end <= other.start:
                return Token.SHADE
        return Token.INTERSECT

    def append_child(self, child):  # type: (Token) -> None
        if not self.etype.parse_children:
            return
        self.children.append(child)

    def as_element(self):  # type: () -> InlineElement
        e = self.etype(self.match)
        if e.parse_children:
            self.children = _resolve_overlap(self.children)
            e.children = make_elements(
                self.children,
                self.text,
                self.inner_start,
                self.inner_end,
                self.fallback,
            )
        return e

    def __repr__(self):  # type: () -> str
        return "<{}: {} start={} end={}>".format(
            self.__class__.__name__, self.etype.__name__, self.start, self.end
        )

    def __lt__(self, o):  # type: (Token) -> bool
        return self.start < o.start


def find_links_or_emphs(text, root_node):  # type: (str, Document) -> List[MatchObj]
    """Fink links/images or emphasis from text.

    :param text: the original text.
    :param root_node: a reference to the root node of the AST.
    :returns: an iterable of match object.
    """
    delimiters_re = re.compile(r"(?:!?\[|\*+|_+)")
    i = 0
    delimiters = []  # type: List[Delimiter]
    escape = False
    matches = []  # type: List[MatchObj]
    code_pattern = re.compile(r"(?<!`)(`+)(?!`)([\s\S]+?)(?<!`)\1(?!`)")

    while i < len(text):
        if escape:
            escape = False
            i += 1
        elif text[i] == "\\":
            escape = True
            i += 1
        elif code_pattern.match(text, i):
            i = code_pattern.match(text, i).end()  # type: ignore
        elif text[i] == "]":
            node = look_for_image_or_link(text, delimiters, i, root_node, matches)
            if node:
                i = node.end()
                matches.append(node)
            else:
                i += 1
        else:
            m = delimiters_re.match(text, i)
            if m:
                delimiters.append(Delimiter(m, text))
                i = m.end()
            else:
                i += 1
    process_emphasis(text, delimiters, None, matches)
    return matches


def look_for_image_or_link(text, delimiters, close, root_node, matches):
    # type: (str, List[Delimiter], int, Document, List[MatchObj]) -> Optional[MatchObj]
    for i, d in list(enumerate(delimiters))[::-1]:
        if d.content not in ("[", "!["):
            continue
        if not d.active:
            break  # break to remove the delimiter and return None
        if not _is_legal_link_text(text[d.end : close]):
            break
        link_text = (d.end, close, text[d.end : close])
        etype = "Image" if d.content == "![" else "Link"
        match = _expect_inline_link(text, close + 1) or _expect_reference_link(
            text, close + 1, link_text[2], root_node
        )
        if not match:  # not a link
            break
        rv = MatchObj(etype, text, d.start, match[2], link_text, match[0], match[1])
        process_emphasis(text, delimiters, i, matches)
        if etype == "Link":
            for d in delimiters[:i]:
                if d.content == "[":
                    d.active = False
        del delimiters[i]
        return rv

    else:
        # no matching opener is found
        return None

    del delimiters[i]
    return None


def _is_legal_link_text(text):  # type: (str) -> bool
    return is_paired(text, "[", "]")


def _expect_inline_link(text, start):
    # type: (str, int) -> Optional[Tuple[Group, Group, int]]
    """(link_dest "link_title")"""
    if start >= len(text) - 1 or text[start] != "(":
        return None
    i = start + 1
    m = patterns.whitespace.match(text, i)
    if m:
        i = m.end()
    m = patterns.link_dest_1.match(text, i)
    if m:
        link_dest = m.start(), m.end(), m.group()
        i = m.end()
    else:
        if text[i] == "<":
            return None
        open_num = 0
        escaped = False
        prev = i
        while i < len(text):
            c = text[i]
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == "(":
                open_num += 1
            elif c in string.whitespace:
                break
            elif c == ")":
                if open_num > 0:
                    open_num -= 1
                else:
                    break
            i += 1
        if open_num != 0:
            return None
        link_dest = prev, i, text[prev:i]
    link_title = i, i, None
    tail_re = re.compile(r"(?:\s+%s)?\s*\)" % patterns.link_title, flags=re.UNICODE)
    m = tail_re.match(text, i)
    if not m:
        return None
    if m.group("title"):
        link_title = m.start("title"), m.end("title"), m.group("title")  # type: ignore
    return (link_dest, link_title, m.end())


def _expect_reference_link(text, start, link_text, root_node):
    # type: (str, int, str, Document) -> Optional[Tuple[Group, Group, int]]
    match = patterns.optional_label.match(text, start)
    link_label = link_text
    if match and match.group()[1:-1]:
        link_label = match.group()[1:-1]
    result = _get_reference_link(link_label, root_node)
    if not result:
        return None
    link_dest = start, start, result[0]
    link_title = start, start, result[1]
    return (link_dest, link_title, match and match.end() or start)


def _get_reference_link(link_label, root_node):
    # type: (str, Document) -> Optional[Tuple[str, str]]
    normalized_label = normalize_label(link_label)
    return root_node.link_ref_defs.get(normalized_label, None)


def process_emphasis(text, delimiters, stack_bottom, matches):
    # type: (str, List[Delimiter], Optional[int], List[MatchObj]) -> None
    star_bottom = underscore_bottom = stack_bottom
    cur = _next_closer(delimiters, stack_bottom)
    while cur is not None:
        d_closer = delimiters[cur]
        bottom = star_bottom if d_closer.content[0] == "*" else underscore_bottom
        opener = _nearest_opener(delimiters, cur, bottom)
        if opener is not None:
            d_opener = delimiters[opener]
            n = 2 if len(d_opener.content) >= 2 and len(d_closer.content) >= 2 else 1
            match = MatchObj(
                "StrongEmphasis" if n == 2 else "Emphasis",
                text,
                d_opener.end - n,
                d_closer.start + n,
                (d_opener.end, d_closer.start, text[d_opener.end : d_closer.start]),
            )
            matches.append(match)
            del delimiters[opener + 1 : cur]
            cur -= cur - opener - 1
            if d_opener.remove(n):
                delimiters.remove(d_opener)
                cur -= 1
            if d_closer.remove(n, True):
                delimiters.remove(d_closer)
            cur = cur - 1 if cur > 0 else None
        else:
            bottom = cur - 1 if cur > 1 else None
            if d_closer.content[0] == "*":
                star_bottom = bottom
            else:
                underscore_bottom = bottom
            if not d_closer.can_open:
                delimiters.remove(d_closer)
        cur = _next_closer(delimiters, cur)
    lower = stack_bottom + 1 if stack_bottom is not None else 0
    del delimiters[lower:]


def _next_closer(delimiters, bound):
    # type: (List[Delimiter], Optional[int]) -> Optional[int]
    i = bound + 1 if bound is not None else 0
    while i < len(delimiters):
        d = delimiters[i]
        if getattr(d, "can_close", False):
            return i
        i += 1
    return None


def _nearest_opener(delimiters, higher, lower):
    # type: (List[Delimiter], int, Optional[int]) -> Optional[int]
    i = higher - 1
    lower = lower if lower is not None else -1
    while i > lower:
        d = delimiters[i]
        if getattr(d, "can_open", False) and d.closed_by(delimiters[higher]):
            return i
        i -= 1
    return None


class Delimiter:
    whitespace_re = re.compile(r"\s", flags=re.UNICODE)

    def __init__(self, match, text):  # type: (_Match, str) -> None
        self.start = match.start()
        self.end = match.end()
        self.content = match.group()
        self.text = text
        self.active = True
        if self.content[0] in ("*", "_"):
            self.can_open = self._can_open()
            self.can_close = self._can_close()

    def _can_open(self):  # type: () -> bool
        if self.content[0] == "*":
            return self.is_left_flanking()
        return self.is_left_flanking() and (
            not self.is_right_flanking() or self.preceded_by_punc()
        )

    def _can_close(self):  # type: () -> bool
        if self.content[0] == "*":
            return self.is_right_flanking()
        return self.is_right_flanking() and (
            not self.is_left_flanking() or self.followed_by_punc()
        )

    def is_left_flanking(self):  # type: () -> bool
        return (
            self.end < len(self.text)
            and self.whitespace_re.match(self.text, self.end) is None
        ) and (
            not self.followed_by_punc()
            or self.start == 0
            or self.preceded_by_punc()
            or self.whitespace_re.match(self.text, self.start - 1) is not None
        )

    def is_right_flanking(self):  # type: () -> bool
        return (
            self.start > 0
            and self.whitespace_re.match(self.text, self.start - 1) is None
        ) and (
            not self.preceded_by_punc()
            or self.end == len(self.text)
            or self.followed_by_punc()
            or self.whitespace_re.match(self.text, self.end) is not None
        )

    def followed_by_punc(self):  # type: () -> bool
        return (
            self.end < len(self.text)
            and patterns.punctuation.match(self.text, self.end) is not None
        )

    def preceded_by_punc(self):  # type: () -> bool
        return (
            self.start > 0
            and patterns.punctuation.match(self.text[self.start - 1]) is not None
        )

    def closed_by(self, other):  # type: (Delimiter) -> bool
        return not (
            self.content[0] != other.content[0]
            or (self.can_open and self.can_close or other.can_open and other.can_close)
            and len(self.content + other.content) % 3 == 0
            and not all(len(d.content) % 3 == 0 for d in [self, other])
        )

    def remove(self, n, left=False):  # type: (int, bool) -> bool
        if len(self.content) <= n:
            return True
        if left:
            self.start += n
        else:
            self.end -= n
        self.content = self.content[n:]
        return False

    def __repr__(self):  # type: () -> str
        return "<Delimiter {!r} start={} end={}>".format(
            self.content, self.start, self.end
        )


class MatchObj:
    """A fake match object that memes re.match methods"""

    def __init__(self, etype, text, start, end, *groups):
        # type: (str, str, int, int, Group) -> None
        self._text = text
        self._start = start
        self._end = end
        self._groups = groups
        self.etype = etype

    def group(self, n=0):  # type: (int) -> str
        if n == 0:
            return self._text[self._start : self._end]
        return self._groups[n - 1][2]  # type: ignore

    def start(self, n=0):  # type: (int) -> int
        if n == 0:
            return self._start
        return self._groups[n - 1][0]

    def end(self, n=0):  # type: (int) -> int
        if n == 0:
            return self._end
        return self._groups[n - 1][1]


if is_type_check():
    _Match = Union[Match, MatchObj]
