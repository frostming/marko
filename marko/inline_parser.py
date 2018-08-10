"""
Parse inline elements
"""


def parse(text, elements, fallback):
    """Parse given text and produce a list of inline elements.

    :param text: the text to be parsed.
    :param elements: the element types to be included in parsing
    :param fallback: fallback class when no other element type is matched.
    """
    # this is a raw list of elements that needs to be processed later.
    parse_buffer = []
    for etype in elements:
        for match in etype.find(text):
            parse_buffer.append(Token(etype, match, text, fallback))
    parse_buffer.sort()


class Token(object):
    """An intermediate class to wrap the match object."""
    PROCEDE = 0
    INTERSECT = 1
    CONTAIN = 2
    SHADE = 3

    def __init__(self, etype, match, text, fallback):
        self.etype = etype
        self.match = match
        self.start = match.start()
        self.end = match.end()
        self.inner_start = match.start(etype.parse_group)
        self.inner_end = match.end(etype.parse_group)
        self.text = text
        self.fallback = fallback

    def relation(self, other):
        if self.end >= other.start:
            return Token.PROCEDE
        if self.end >= other.end:
            if other.start >= self.inner_start and other.end <= self.inner_end:
                return Token.CONTAIN
            if self.inner_end <= other.start:
                return Token.SHADE
        return Token.INTERSECT
