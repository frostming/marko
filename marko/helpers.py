"""
Helper functions and data structures
"""
import functools
import re
from contextlib import contextmanager
from importlib import import_module


def camel_to_snake_case(name):  # type: (str) -> str
    """Takes a camelCased string and converts to snake_case."""
    pattern = r"[A-Z][a-z]+|[A-Z]+(?![a-z])"
    return "_".join(map(str.lower, re.findall(pattern, name)))


def is_paired(text, open="(", close=")"):  # type: (str, str, str) -> bool
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


def _preprocess_text(text):  # type: (str) -> str
    return text.replace("\r\n", "\n")


class Source:
    """Wrapper class on content to be parsed"""

    def __init__(self, text):  # type: (str) -> None
        self._buffer = _preprocess_text(text)
        self.pos = 0
        self._anchor = 0
        self._states = []  # type: List[BlockElement]
        self.match = None  # type: Optional[Match]

    @property
    def state(self):  # type: () -> BlockElement
        """Returns the current element state."""
        if not self._states:
            raise RuntimeError("Need to push a state first.")
        return self._states[-1]

    @property
    def root(self):  # type: () -> BlockElement
        """Returns the root element, which is at the bottom of self._states."""
        if not self._states:
            raise RuntimeError("Need to push a state first.")
        return self._states[0]

    def push_state(self, element):  # type: (BlockElement) -> None
        """Push a new state to the state stack."""
        self._states.append(element)

    def pop_state(self):  # type: () -> BlockElement
        """Pop the top most state."""
        return self._states.pop()

    @contextmanager
    def under_state(self, element):
        # type: (BlockElement) -> Generator[Source, None, None]
        """A context manager to enable a new state temporarily."""
        self.push_state(element)
        yield self
        self.pop_state()

    @property
    def exhausted(self):  # type: () -> bool
        """Indicates whether the source reaches the end."""
        return self.pos >= len(self._buffer)

    @property
    def prefix(self):  # type: () -> str
        """The prefix of each line when parsing."""
        return "".join(s._prefix for s in self._states)

    def _expect_re(self, regexp, pos):
        # type: (Union[Pattern, str], int) -> Optional[Match]
        if isinstance(regexp, str):
            regexp = re.compile(regexp)
        return regexp.match(self._buffer, pos)

    @staticmethod
    @functools.lru_cache()
    def match_prefix(prefix, line):  # type: (str, str) -> int
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

    def expect_re(self, regexp):  # type: (Union[Pattern, str]) -> Optional[Match]
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

    def next_line(self, require_prefix=True):  # type: (bool) -> Optional[str]
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

    def consume(self):  # type: () -> None
        """Consume the body of source. ``pos`` will move forward."""
        if self.match:
            self.pos = self.match.end()
            if self.match.group()[-1:] == "\n":
                self._update_prefix()
            self.match = None

    def anchor(self):  # type: () -> None
        """Pin the current parsing position."""
        self._anchor = self.pos

    def reset(self):  # type: () -> None
        """Reset the position to the last anchor."""
        self.pos = self._anchor

    def _update_prefix(self):  # type: () -> None
        for s in self._states:
            if hasattr(s, "_second_prefix"):
                s._prefix = s._second_prefix  # type: ignore


def normalize_label(label):  # type: (str) -> str
    """Return the normalized form of link label."""
    return re.sub(r"\s+", " ", label).strip().casefold()


def load_extension_object(name):
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
        except ImportError:
            raise ImportError(
                f"Extension {name} cannot be found. Please check the name."
            )

    try:
        maker = getattr(module, "make_extension")
    except AttributeError:
        raise AttributeError(
            f"Module {name} does not have 'make_extension' attributte."
        )
    return maker


def is_type_check() -> bool:  # pragma: no cover
    try:
        from typing import TYPE_CHECKING
    except ImportError:
        return False
    else:
        return TYPE_CHECKING


if is_type_check():
    from .block import BlockElement
    from typing import Optional, List, Generator, Union, Pattern, Match
