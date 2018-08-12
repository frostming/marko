"""
Parse inline elements
"""


def parse(text, elements, fallback):
    """Parse given text and produce a list of inline elements.

    :param text: the text to be parsed.
    :param elements: the element types to be included in parsing
    :param fallback: fallback class when no other element type is matched.
    """
    # this is a raw list of elements that may contain overlaps.
    tokens = []
    for etype in elements:
        for match in etype.find(text):
            tokens.append(Token(etype, match, text, fallback))
    tokens.sort()
    tokens = _resolve_overlap(tokens)
    return make_elements(tokens, text, fallback=fallback)


def _resolve_overlap(tokens):
    if not tokens:
        return tokens
    result = []
    prev = tokens[0]
    for cur in tokens[1:]:
        r = prev.relation(cur)
        if r == Token.PROCEDE:
            result.append(prev)
            prev = cur
        elif r == Token.CONTAIN:
            prev.append_child(cur)
        elif r == Token.INTERSECT and prev.etype.priority < cur.etype.priority:
            prev = cur
    result.append(prev)
    return result


def make_elements(tokens, text, start=0, end=None, fallback=None):
    """Make elements from a list of parsed tokens.
    It will turn all unmatched holes into fallback elements.

    :param tokens: a list of parsed tokens.
    :param text: the original tet.
    :param start: the offset of where parsing starts. Defaults to the start of text.
    :param end: the offset of where parsing ends. Defauls to the end of text.
    :param fallback: fallback element type.
    :returns: a list of inline elements.
    """
    result = []
    end = end or len(text)
    prev_end = start
    for token in tokens:
        if prev_end < token.start:
            result.append(fallback(text[prev_end:token.start]))
        result.append(token.as_element())
        prev_end = token.end
    if prev_end < end:
        result.append(fallback(text[prev_end:end]))
    return result


class Token(object):
    """An intermediate class to wrap the match object.
    It can be converted to element by :meth:`as_element()`
    """
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
        self.children = []

    def relation(self, other):
        if self.end >= other.start:
            return Token.PROCEDE
        if self.end >= other.end:
            if other.start >= self.inner_start and other.end <= self.inner_end:
                return Token.CONTAIN
            if self.inner_end <= other.start:
                return Token.SHADE
        return Token.INTERSECT

    def append_child(self, child):
        if not self.etype.parse_children:
            return
        self.children.append(child)

    def as_element(self):
        self.children = _resolve_overlap(self.children)
        e = self.etype(self.match)
        e.children = make_elements(
            self.children, self.text, self.start, self.end, self.fallback
        )
        return e

    def __repr__(self):
        return '<{}: {} start={} end={}>'.format(
            self.__class__.__name__, self.etype, self.start, self.end
        )

    def __lt__(self, o):
        return self.start < o.start
