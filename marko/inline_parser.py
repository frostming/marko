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
        """
