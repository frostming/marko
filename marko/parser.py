#! -*- coding: utf-8 -*-
"""
parser function
"""
import re
from contextlib import contextmanager

from ._compat import string_types
from . import block, inline, scanner as scan_module


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
        return self._buffer[self.pos :]

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

    def expect_element(self, element_type):
        """Check whether the rest of source matches the given element type."""
        return block._element_types[element_type].match(self)

    def next_line(self, consume=False, require_prefix=True):
        """"""
        lf = self._buffer.find('\n', self.pos)
        if lf < 0:
            lf = len(self._buffer) - 1
        line = self._buffer[self.pos : lf + 1]
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
            if isinstance(s, block.ListItem):
                s._prefix = s._second_prefix


def parse(source):
    """Parses given text into AST"""
    block_elements = block.get_elements()
    if isinstance(source, string_types):
        source = Source(source)
    ast = []
    while not source.exhausted:
        for name, ele_type in block_elements:
            if ele_type.match(source):
                result = ele_type.parse(source)
                if not isinstance(result, block.BlockElement):
                    result = ele_type(result)
                ast.append(result)
                break
        else:
            # Quit the current parsing and go back to higher level parsing
            break
    return ast


# Only generates at the first time and use cache then.
_scanner = None


def parse_inline(text):
    """Use re.Scanner to parse inline tokens"""
    elements = inline.get_elements()
    scanner = _scanner_for(elements)
    ast = []
    for name, match in scanner.scan_with_holes(text):
        element_type = inline._element_types[name]
        ast.append(element_type(match))
    return ast


def _scanner_for(elements):
    global _scanner
    if _scanner:
        return _scanner
    rules = [
        (name, pattern)
        for name, element in elements
        for pattern in element.patterns
    ]
    _scanner = scan_module.Scanner(rules, re.M)
    return _scanner
