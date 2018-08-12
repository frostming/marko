#! -*- coding: utf-8 -*-
"""
Inline(span) level elements
"""
import re
from .helpers import string_types
from . import parser_inline

# backrefs to avoid cylic  import
parser = None
_root_node = None

__all__ = ('LineBreak', 'Literal', 'LinkOrEmph', 'InlineHTML', 'CodeSpan',
           'Emphasis', 'StrongEmphasis', 'Link', 'Image', 'RawText')


class InlineElement(object):
    """Any inline element should inherit this class"""

    #: Use to denote the precedence in parsing.
    priority = 5
    #: element regex pattern.
    pattern = None
    #: whether to parse children.
    parse_children = False
    #: which match group to parse.
    parse_group = 1
    #: if True, it won't be included in parsing process but produced by other elements
    #: other elements instead.
    virtual = False

    def __init__(self, match):
        """Parses the matched object into an element"""
        if not self.parse_children:
            self.children = match.group(self.parse_group)

    @classmethod
    def find(cls, text):
        """This method should return an iterable containing matches of this element."""
        if isinstance(cls.pattern, string_types):
            cls.pattern = re.compile(cls.pattern)
        return cls.pattern.finditer(text)


class Literal(InlineElement):
    """Literal escapes need to be parsed at the first."""
    priority = 9
    pattern = re.compile(r'\\[!"#\$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]')

    def __init__(self, match):
        self.children = match.group()[1:]


class LineBreak(InlineElement):
    """Line breaks:
    Soft: '\n'
    Hard: '  \n'
    """
    priority = 2
    pattern = re.compile(r'( *|\\)\n')

    def __init__(self, match):
        self.soft = match.group(1).startswith(('  ', '\\'))


class InlineHTML(InlineElement):

    pattern = (
        r'(?:<%s(?:%s)* */?>'    # open tag
        r'|</%s *>'              # closing tag
        r'|<!--(?!>|->|[\s\S]*?--[\s\S]*?-->)[\s\S]*?-->'   # HTML comment
        r'|<\?[\s\S]*?\?>'       # processing instruction
        r'|<![A-Z]+ +[\s\S]*?>'  # declaration
        r'|<!\[CDATA\[[\s\S]*?\]\]>)'                       # CDATA section
    )

    def __init__(self, match):
        self.children = match.group(0)


class LinkOrEmph(InlineElement):
    """This is a special element, whose parsing is done specially.
    And it produces Link or Emphasis elements.
    """

    def __new__(cls, match):
        return parser.inline_elements[match.type](match)

    @classmethod
    def find(cls, text):
        return parser_inline.find_links_or_emphs(text, _root_node)


class StrongEmphasis(InlineElement):
    """Strong emphasis: **sample text**"""
    virtual = True


class Emphasis(InlineElement):
    """Emphasis: *sample text*"""
    virtual = True


class Link(InlineElement):
    """Link: [text](/link/destination)"""
    virtual = True


class Image(InlineElement):
    """Image: ![alt](/src/address)"""
    virtual = True


class CodeSpan(InlineElement):

    priority = 7
    pattern = re.compile(r'(`+)([\s\S]+?)(?<!`)\1(?!`)')

    def __init__(self, match):
        self.children = re.sub(r'\s+', ' ', match.group(2).strip())


class Url(InlineElement):

    priority = 1


class AutoLink(InlineElement):
    priority = 7
    patterns = (r'<[^>]+>',)

    @classmethod
    def parse(cls, match):
        return {'link': match.group(0)[1:-1]}


class RawText(InlineElement):
    """The raw text is the fallback for all holes that doesn't match any others."""
    virtual = True

    def __init__(self, match):
        self.children = match
