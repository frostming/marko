from __future__ import annotations

import functools
import re
import types
from collections.abc import Generator
from contextlib import contextmanager
from re import Match, Pattern
from typing import TYPE_CHECKING, cast, overload

from marko.block import BlockElement, Document

if TYPE_CHECKING:
    from typing import Literal

    from marko.parser import Parser


_LINE_RE = re.compile(r"(?m)[^\n]*$\n?")
_LAZY_LINE_RE = re.compile(r"(?m)[^\n]*?$\n?")


def _preprocess_text(text: str) -> str:
    # Normalize line terminators so block parsers can always advance on line reads.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\x00", "�")


class Source:
    """Wrapper class on content to be parsed"""

    parser: Parser

    def __init__(self, text: str) -> None:
        self._buffer = _preprocess_text(text)
        self.pos = 0
        self._anchor = 0
        self._states: list[BlockElement] = []
        self._prefix_cache: str | None = None
        self.match: Match[str] | None = None
        #: (pos, prefix, prefix length, line match) of the last prefix check, since
        #: every block element tried on a line checks the same prefix again.
        self._line_prefix: tuple[int, str, int, Match[str] | None] = (-1, "", 0, None)
        #: Store temporary data during parsing.
        self.context = types.SimpleNamespace()

    @property
    def state(self) -> BlockElement:
        """Returns the current element state."""
        if not self._states:
            raise RuntimeError("Need to push a state first.")
        return self._states[-1]

    @property
    def root(self) -> Document:
        """Returns the root element, which is at the bottom of self._states."""
        if not self._states:
            raise RuntimeError("Need to push a state first.")
        return cast(Document, self._states[0])

    def push_state(self, element: BlockElement) -> None:
        """Push a new state to the state stack."""
        self._states.append(element)
        self._prefix_cache = None

    def pop_state(self) -> BlockElement:
        """Pop the top most state."""
        self._prefix_cache = None
        return self._states.pop()

    @contextmanager
    def under_state(self, element: BlockElement) -> Generator[Source, None, None]:
        """A context manager to enable a new state temporarily."""
        self.push_state(element)
        try:
            yield self
        finally:
            self.pop_state()

    @property
    def exhausted(self) -> bool:
        """Indicates whether the source reaches the end."""
        return self.pos >= len(self._buffer)

    @property
    def prefix(self) -> str:
        """The prefix of each line when parsing."""
        if self._prefix_cache is None:
            self._prefix_cache = "".join(s._prefix for s in self._states)
        return self._prefix_cache

    @property
    def _current_pos(self) -> int:
        """Return the current source offset after the active block prefixes."""
        match = self._expect_re(_LINE_RE, self.pos)
        if match is None:
            return self.pos
        prefix_len = self.match_prefix(self.prefix, match.group())
        return self.pos + max(prefix_len, 0)

    def _expect_re(self, regexp: Pattern[str] | str, pos: int) -> Match[str] | None:
        if isinstance(regexp, str):
            regexp = re.compile(regexp)
        return regexp.match(self._buffer, pos)

    @staticmethod
    @functools.lru_cache
    def match_prefix(prefix: str, line: str) -> int:
        """Check if the line starts with given prefix and
        return the position of the end of prefix.
        If the prefix is not matched, return -1.
        """
        m = re.match(prefix, line.expandtabs(4))
        if not m:
            if re.match(prefix, line.expandtabs(4).replace("\n", " " * 99 + "\n")):
                return len(line) - 1
            return -1
        pos = m.end()
        if pos == 0:
            return 0
        for i in range(1, len(line) + 1):
            if len(line[:i].expandtabs(4)) >= pos:
                return i
        return -1  # pragma: no cover

    def expect_re(self, regexp: Pattern[str] | str) -> Match[str] | None:
        """Test against the given regular expression and returns the match object.
        :param regexp: the expression to be tested.
        :returns: the match object.
        """
        prefix = self.prefix
        # An empty prefix always matches, so skip reading the whole line.
        if not prefix:
            prefix_len = 0
        else:
            pos, last_prefix, prefix_len, line_match = self._line_prefix
            if pos == self.pos and last_prefix == prefix:
                self.match = line_match
            else:
                line = self.next_line(require_prefix=False)
                prefix_len = self.match_prefix(prefix, line)
                self._line_prefix = (self.pos, prefix, prefix_len, self.match)
        if prefix_len >= 0:
            match = self._expect_re(regexp, self.pos + prefix_len)
            self.match = match
            return match
        else:
            return None

    @overload
    def next_line(self, require_prefix: Literal[False] = ...) -> str: ...

    @overload
    def next_line(self, require_prefix: Literal[True] = ...) -> str | None: ...

    def next_line(self, require_prefix: bool = True) -> str | None:
        """Return the next line in the source.

        :param require_prefix:  if False, the whole line will be returned.
            otherwise, return the line with prefix stripped or None if the prefix
            is not matched.
        """
        if require_prefix:
            m = self.expect_re(_LAZY_LINE_RE)
        else:
            m = self._expect_re(_LINE_RE, self.pos)
        self.match = m
        if m:
            return m.group()
        return None

    def consume(self) -> None:
        """Consume the body of source. ``pos`` will move forward."""
        if self.match:
            self.pos = self.match.end()
            if self.match.group()[-1:] == "\n":
                self._update_prefix()
            self.match = None

    def anchor(self) -> None:
        """Pin the current parsing position."""
        self._anchor = self.pos

    def reset(self) -> None:
        """Reset the position to the last anchor."""
        self.pos = self._anchor

    def _update_prefix(self) -> None:
        self._prefix_cache = None
        for s in self._states:
            if hasattr(s, "_second_prefix"):
                s._prefix = s._second_prefix
