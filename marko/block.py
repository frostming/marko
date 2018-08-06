#! -*- coding: utf-8 -*-
"""
Block level elements
"""
import re
from . import inline

_element_types = {}
_root_node = None

_block_tags = [
    'address', 'article', 'aside', 'base', 'basefont', 'blockquote',
    'body', 'caption', 'center', 'col', 'colgroup', 'dd', 'details',
    'dialog', 'dir', 'div', 'dl', 'dt', 'fieldset', 'figcaption',
    'figure', 'footer', 'form', 'frame', 'frameset', 'h1', 'h2',
    'h3', 'h4', 'h5', 'h6', 'head', 'header', 'hr', 'html', 'iframe',
    'legend', 'li', 'link', 'main', 'menu', 'menuitem', 'meta',
    'nav', 'noframes', 'ol', 'optgroup', 'option', 'p', 'param',
    'section', 'source', 'summary', 'table', 'tbody', 'td', 'tfoot',
    'th', 'thead', 'title', 'tr', 'track', 'ul'
]


def add_element(element_type, override=False):
    """Add a block element.

    :param element_type: the element type class.
    :param override: whether to replace the element type that bases.
    """
    if not override:
        _element_types[element_type.__name__] = element_type
    else:
        for cls in element_type.__mro__:
            if cls in _element_types.values():
                _element_types[cls.__name__] = element_type
                break
        else:
            _element_types[element_type.__name__] = element_type


def get_elements():
    return sorted(_element_types.values(), lambda e: e.priority)


class BlockElement(object):

    tight = False

    @classmethod
    def match(self, source):
        """Test if the source matches the element at current position.

        rtype: bool
        """
        raise NotImplementedError()

    @classmethod
    def parse(self, source):
        """Parses the source. This is a proper place to consume the source body and
        return an element or information to build one. The information tuple will be
        passed to ``__init__`` method afterwards. Inline parsing, if any, should also
        be performed here."""
        raise NotImplementedError()


class Document(BlockElement):
    """Document node element."""

    def __init__(self, source):
        self.prefix = ''
        self.footnotes = []
        self.link_ref_defs = {}
        global _root_node
        _root_node = self
        inline._root_node = self
        with source.under_state(self):
            self.children = parser.parse(source)
        _root_node = None
        inline._root_node = None


class BlankLine(BlockElement):
    """Blank lines"""
    priority = 5
    pattern = re.compile(r'\n+')

    @classmethod
    def match(cls, source):
        return source.expect_re(cls.pattern)

    @classmethod
    def parse(cls, source):
        source.expect_re(cls.pattern, True)
        source.state.tight = False
        return cls()


class Heading(BlockElement):
    """Heading element: (### Hello\n)"""
    priority = 6
    pattern = re.compile(r'^ {0,3}(#{1,6})( [^\n]*?| *)(?:(?<= )(?<!\\)#+)? *$\n?')

    def __init__(self, match):
        self.level = len(match.group(1))
        self.children = parser.parse_inline(match.group(2).strip())

    @classmethod
    def match(cls, source):
        return source.expect_re(cls.pattern)

    @classmethod
    def parse(cls, source):
        return source.expect_re(cls.pattern, True)


class SetextHeading(BlockElement):
    """Setext heading: (Hello\n===\n)
    It won't be parsed directly, will be created by ``Paragraph.__new__`` instead.
    """
    pass


class CodeBlock(BlockElement):
    """Indented code block: (    this is a code block\n)"""
    priority = 9

    def __init__(self, lines):
        self.content = inline.get_elements()['RawText'](lines)

    @classmethod
    def match(cls, source):
        return source.expect_re(r' {4}')

    @classmethod
    def parse(cls, source):
        lines = [source.next_line(True)[4:]]
        while not source.exhausted:
            if source.expect_re(r' {4}'):
                lines.append[source.next_line(True)[4:]]
                source.anchor()
            elif not source.next_line().strip():
                lines.append(source.next_line(True))
            else:
                source.reset()
                break
        return ''.join(lines).rstrip('\n') + '\n'


class FencedCode(BlockElement):
    """Fenced code block: (```python\nhello\n```\n)"""
    priority = 7
    pattern = r'( {,3})(`{3,}|~{3,}) *(\S*)(.*?)$'
    _parse_info = None

    def __init__(self, match):
        self.lang = match[0]
        self.children = inline.get_elements()['RawText'](match[1])

    @classmethod
    def match(cls, source):
        m = source.expect_re(cls.pattern)
        if not m:
            return False
        prefix, leading, lang, tail = m.groups()
        if leading[0] in lang or leading[0] in tail:
            return False
        cls._parse_info = prefix, leading, lang
        return True

    @classmethod
    def parse(cls, source):
        source.next_line(True)
        lines = []
        while not source.exhausted:
            line = source.next_line(True)
            m = re.match(r' {,3}(~+|`+) *$', line)
            if m and cls._parse_info[1] in m.group(1):
                break

            prefix_len = source.match_prefix(cls._parse_info[0], line)
            if prefix_len >= 0:
                line = line[prefix_len:]
            lines.append(line)
        return cls._parse_info[2], ''.join(lines)


class ThematicBreak(BlockElement):
    """Horizontal rules: (----\n)"""
    priority = 8
    pattern = re.compile(r' {,3}([-=+] *){3,}$\n?')

    @classmethod
    def match(cls, source):
        m = source.expect_re(cls.pattern)
        if not m:
            return False
        return len(set(re.sub(r'\s+', '', m.group()))) == 1

    @classmethod
    def parse(cls, source):
        source.next_line(True)
        return cls()


class HTMLBlock(BlockElement):
    """HTML blocks, parsed as it is"""
    priority = 5
    _end_cond = None

    def __init__(self, lines):
        self.children = lines

    @classmethod
    def match(cls, source):
        if source.expect_re(r' {,3}<(?:script|pre|style)(?: *|>|$)(?i)'):
            cls._end_cond = re.compile(r'</(?:script|pre|style)>(?i)')
            return 1
        if source.expect_re(r' {,3}<!--'):
            cls._end_cond = re.compile(r'-->')
            return 2
        if source.expect_re(r' {,3}<\?'):
            cls._end_cond = re.compile(r'\?>')
            return 3
        if source.expect_re(r' {,3}<!'):
            cls._end_cond = re.compile(r'>')
            return 4
        if source.expect_re(r' {,3}<!\[CDATA\['):
            cls._end_cond = re.compile(r'\]\]>')
            return 5
        block_tag = r'(?:%s)' % ('|'.join(_block_tags),)
        if source.expect_re(r' {,3}</?%s(?: +|/?>|$)' % block_tag):
            cls._end_cond = None
            return 6
        if source:
            cls._end_cond = None
            return 7

        return False

    @classmethod
    def parse(cls, source):
        lines = [source.next_line(True)]
        while not source.exhausted:
            line = source.next_line()
            lines.append(line)
            if cls._end_cond is not None:
                if cls._end_cond.search(line):
                    source.next_line(True)
                    break
            elif line.strip() == '':
                lines.pop()
                break
            source.next_line(True)
        return ''.join(lines)


# import parsers here to avoid cyclic import
from . import parser    # noqa
