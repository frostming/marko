"""
Helper functions and data structures
"""
from __future__ import annotations

import functools
import re
from contextlib import contextmanager
from importlib import import_module
from typing import (
    TYPE_CHECKING,
    Callable,
    Container,
    Generator,
    Iterable,
    Match,
    Pattern,
)

if TYPE_CHECKING:

    from .block import BlockElement


def camel_to_snake_case(name: str) -> str:
    """Takes a camelCased string and converts to snake_case."""
    pattern = r"[A-Z][a-z]+|[A-Z]+(?![a-z])"
    return "_".join(map(str.lower, re.findall(pattern, name)))


def is_paired(text: Iterable[str], open: str = "(", close: str = ")") -> bool:
    """Check if the text only contains:
    1. blackslash escaped parentheses, or
    2. parentheses paired.
    """
    count = 0
    escape = False
    for c in text:
        if escape:
            escape = False
        elif c == "\\":
            escape = True
        elif c == open:
            count += 1
        elif c == close:
            if count == 0:
                return False
            count -= 1
    return count == 0


def _preprocess_text(text: str) -> str:
    return text.replace("\r\n", "\n")


class Source:
    """Wrapper class on content to be parsed"""

    def __init__(self, text: str) -> None:
        self._buffer = _preprocess_text(text)
        self.pos = 0
        self._anchor = 0
        self._states: list[BlockElement] = []
        self.match: Match[str] | None = None

    @property
    def state(self) -> BlockElement:
        """Returns the current element state."""
        if not self._states:
            raise RuntimeError("Need to push a state first.")
        return self._states[-1]

    @property
    def root(self) -> BlockElement:
        """Returns the root element, which is at the bottom of self._states."""
        if not self._states:
            raise RuntimeError("Need to push a state first.")
        return self._states[0]

    def push_state(self, element: BlockElement) -> None:
        """Push a new state to the state stack."""
        self._states.append(element)

    def pop_state(self) -> BlockElement:
        """Pop the top most state."""
        return self._states.pop()

    @contextmanager
    def under_state(self, element: BlockElement) -> Generator[Source, None, None]:
        """A context manager to enable a new state temporarily."""
        self.push_state(element)
        yield self
        self.pop_state()

    @property
    def exhausted(self) -> bool:
        """Indicates whether the source reaches the end."""
        return self.pos >= len(self._buffer)

    @property
    def prefix(self) -> str:
        """The prefix of each line when parsing."""
        return "".join(s._prefix for s in self._states)

    def _expect_re(self, regexp: Pattern[str] | str, pos: int) -> Match[str] | None:
        if isinstance(regexp, str):
            regexp = re.compile(regexp)
        return regexp.match(self._buffer, pos)

    @staticmethod
    @functools.lru_cache()
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
        prefix_len = self.match_prefix(
            self.prefix, self.next_line(require_prefix=False)  # type: ignore
        )
        if prefix_len >= 0:
            match = self._expect_re(regexp, self.pos + prefix_len)
            self.match = match
            return match
        else:
            return None

    def next_line(self, require_prefix: bool = True) -> str | None:
        """Return the next line in the source.

        :param require_prefix:  if False, the whole line will be returned.
            otherwise, return the line with prefix stripped or None if the prefix
            is not matched.
        """
        if require_prefix:
            m = self.expect_re(r"(?m)[^\n]*?$\n?")
        else:
            m = self._expect_re(r"(?m)[^\n]*$\n?", self.pos)
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
        for s in self._states:
            if hasattr(s, "_second_prefix"):
                s._prefix = s._second_prefix  # type: ignore


def normalize_label(label: str) -> str:
    """Return the normalized form of link label."""
    return re.sub(r"\s+", " ", label).strip().casefold()


def find_next(
    text: str,
    target: Container[str],
    start: int = 0,
    end: int | None = None,
    disallowed: Container[str] = (),
) -> int:
    """Find the next occurrence of target in text, and return the index
    Characters are escaped by backslash.
    Optional disallowed characters can be specified, if found, the search
    will fail with -2 returned. Otherwise, -1 is returned if not found.
    """
    if end is None:
        end = len(text)
    i = start
    escaped = False
    while i < end:
        c = text[i]
        if escaped:
            escaped = False
        elif c in target:
            return i
        elif c in disallowed:
            return -2
        elif c == "\\":
            escaped = True
        i += 1
    return -1


def partition_by_spaces(text: str, spaces: str = " \t") -> tuple[str, str, str]:
    """Split the given text by spaces or tabs, and return a tuple of
    (start, delimiter, remaining). If spaces are not found, the latter
    two elements will be empty.
    """
    start = end = -1
    for i, c in enumerate(text):
        if c in spaces:
            if start >= 0:
                continue
            start = i
        elif start >= 0:
            end = i
            break
    if start < 0:
        return text, "", ""
    if end < 0:
        return text[:start], text[start:], ""
    return text[:start], text[start:end], text[end:]


def load_extension_object(name: str) -> Callable:
    """Load extension object from a string.
    First try `marko.ext.<name>` if possible
    """
    module = None
    if "." not in name:
        try:
            module = import_module(f"marko.ext.{name}")
        except ImportError:
            pass
    if module is None:
        try:
            module = import_module(name)
        except ImportError as e:
            raise ImportError(f"Extension {name} cannot be imported") from e

    try:
        return module.make_extension
    except AttributeError:
        raise AttributeError(
            f"Module {name} does not have 'make_extension' attributte."
        ) from None
