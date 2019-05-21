"""
Helper functions and data structures
"""
import re
from contextlib import contextmanager

from ._compat import string_types


def camel_to_snake_case(name):
    """Takes a camelCased string and converts to snake_case."""
    pattern = r"[A-Z][a-z]+|[A-Z]+(?![a-z])"
    return "_".join(map(str.lower, re.findall(pattern, name)))


def is_paired(text, open="(", close=")"):
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


def _preprocess_text(text):
    return text.replace("\r\n", "\n")


class Source(object):
    """Wrapper class on content to be parsed"""

    def __init__(self, text):
        self._buffer = _preprocess_text(text)
        self.pos = 0
        self._anchor = 0
        self._states = []
        self.match = False

    @property
    def state(self):
        """Returns the current element state."""
        if not self._states:
            return None
        return self._states[-1]

    @property
    def root(self):
        """Returns the root element, which is at the bottom of self._states."""
        if not self._states:
            return None
        return self._states[0]

    def push_state(self, element):
        """Push a new state to the state stack."""
        self._states.append(element)

    def pop_state(self):
        """Pop the top most state."""
        return self._states.pop()

    @contextmanager
    def under_state(self, element):
        """A context manager to enable a new state temporarily."""
        self.push_state(element)
        yield self
        self.pop_state()

    @property
    def exhausted(self):
        """Indicates whether the source reaches the end."""
        return self.pos >= len(self._buffer)

    @property
    def prefix(self):
        """The prefix of each line when parsing."""
        return "".join(s._prefix for s in self._states)

    @property
    def rest(self):
        """The remaining source unparsed."""
        return self._buffer[self.pos :]

    def _expect_re(self, regexp, pos):
        if isinstance(regexp, string_types):
            regexp = re.compile(regexp)
        return regexp.match(self._buffer, pos)

    @staticmethod
    def match_prefix(prefix, line):
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

    def expect_re(self, regexp):
        """Test against the given regular expression and returns the match object.

        :param regexp: the expression to be tested.
        :returns: the match object.
        """
        prefix_len = self.match_prefix(
            self.prefix, self.next_line(require_prefix=False)
        )
        if prefix_len >= 0:
            match = self._expect_re(regexp, self.pos + prefix_len)
            self.match = match
            return match
        else:
            return None

    def next_line(self, require_prefix=True):
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

    def consume(self):
        """Consume the body of source. ``pos`` will move forward."""
        if self.match:
            self.pos = self.match.end()
            if self.match.group()[-1] == "\n":
                self._update_prefix()
            self.match = None

    def anchor(self):
        """Pin the current parsing position."""
        self._anchor = self.pos

    def reset(self):
        """Reset the position to the last anchor."""
        self.pos = self._anchor

    def _update_prefix(self):
        for s in self._states:
            if hasattr(s, "_second_prefix"):
                s._prefix = s._second_prefix


def normalize_label(label):
    """Return the normalized form of link label."""
    return re.sub(r"\s+", " ", label).strip().lower()
