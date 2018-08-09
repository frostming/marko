"""
Helper functions and data structures
"""
import re
from contextlib import contextmanager

from ._compat import string_types

camelcase_re = re.compile(r'([A-Z]+)(?=[a-z0-9])')


def camel_to_snake_case(name):
    """Takes a camelCased string and converts to snake_case."""
    def _join(match):
        word = match.group()

        if len(word) > 1:
            return ('_%s_%s' % (word[:-1], word[-1])).lower()

        return '_' + word.lower()

    return camelcase_re.sub(_join, name).lstrip('_')


def is_parenthesis_paired(text):
    """Check if the text only contains:
    1. blackslash escaped parentheses, or
    2. parentheses paired.
    """
    count = 0
    escape = False
    for c in text:
        if escape:
            escape = False
        elif c == '\\':
            escape = True
        elif c == '(':
            count += 1
        elif c == ')':
            if count == 0:
                return False
            count -= 1
    return count == 0


def _preprocess_text(text):
    return re.sub(r'^ +$', '', text, flags=re.M).replace('\r\n', '\n')


class Source(object):
    """Wrapper class on content to be parsed"""

    def __init__(self, text):
        self._buffer = _preprocess_text(text)
        self.pos = 0
        self._anchor = 0
        self._states = []

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
        return ''.join(s._prefix for s in self._states)

    @property
    def rest(self):
        """The remaining source unparsed."""
        return self._buffer[self.pos:]

    def _expect_re(self, regexp):
        if isinstance(regexp, string_types):
            regexp = re.compile(regexp)
        return regexp.match(self._buffer, self.pos)

    @staticmethod
    def match_prefix(prefix, line):
        """Check if the line starts with given prefix and
        return the position of the end of prefix.
        If the prefix is not matched, return -1.
        """
        if re.match(prefix, ' ' * 999) and not line.strip():
            return 0
        m = re.match(prefix, line.expandtabs(4))
        if not m:
            return -1
        pos = m.end()
        if pos == 0:
            return 0
        for i in range(1, len(line) + 1):
            if len(line[:i].expandtabs(4)) >= pos:
                return i

    def expect_re(self, regexp, consume=False):
        """Test against the given regular expression and returns the match object.

        :param regexp: the expression to be tested.
        :param consume: whether to consume the body of source.
        :returns: the match object.
        """
        prefix_len = self.match_prefix(
            self.prefix, self.next_line(require_prefix=False)
        )
        if prefix_len >= 0:
            self.anchor()
            self.pos += prefix_len
            rv = self._expect_re(regexp)
            if rv and consume:
                self.pos = rv.end()
                if rv.group()[-1] == '\n':
                    self._update_prefix()
            else:
                self.reset()
            return rv
        else:
            return None

    def next_line(self, consume=False, require_prefix=True):
        """"""
        lf = self._buffer.find('\n', self.pos)
        if lf < 0:
            lf = len(self._buffer) - 1
        line = self._buffer[self.pos:lf + 1]
        if require_prefix:
            prefix_len = self.match_prefix(self.prefix, line)
            if prefix_len < 0:
                return None
            line = line[prefix_len:]
        if consume:
            self.pos = lf + 1
            self._update_prefix()
        return line

    def anchor(self):
        self._anchor = self.pos

    def reset(self):
        self.pos = self._anchor

    def _update_prefix(self):
        for s in self._states:
            if hasattr(s, '_second_prefix'):
                s._prefix = s._second_prefix


def scan_inline(text, elements):
    """Scans the text and return a generator of inline elements.
    Any holes that don't match any elements will be thrown as-is.

    :param text: the text to be parsed.
    :param elements: a list of element types to be included in parsing.
    :returns: a generator of elements or holes.
    """
    def find_first(text):
        first = 1 << 32
        pair = (None, None)

        for e in elements:
            match = e.search(text)
            if not match:
                continue
            if match.start() < first:
                pair = (e, match)
            first = match.start()
        return pair

    while text:
        e, match = find_first(text)
        if not e:
            break
        if match.start() > 0:
            yield text[: match.start()]
        yield e(match)
        text = text[match.end():]
    if text:
        yield text
