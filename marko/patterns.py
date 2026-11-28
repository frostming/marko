"""
Some regex patterns
"""

import functools
import re
import string
import unicodedata
from collections.abc import Iterator

tags = [
    "address",
    "article",
    "aside",
    "base",
    "basefont",
    "blockquote",
    "body",
    "caption",
    "center",
    "col",
    "colgroup",
    "dd",
    "details",
    "dialog",
    "dir",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "frame",
    "frameset",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hr",
    "html",
    "iframe",
    "legend",
    "li",
    "link",
    "main",
    "menu",
    "menuitem",
    "meta",
    "nav",
    "noframes",
    "ol",
    "optgroup",
    "option",
    "p",
    "param",
    "section",
    "source",
    "summary",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "title",
    "tr",
    "track",
    "ul",
]
tag_name = r"[A-Za-z][A-Za-z0-9\-]*"
attribute = (
    r"\s+[A-Za-z:_][A-Za-z0-9\-_\.:]*"
    r'(?:\s*=\s*(?:[^\s"\'`=<>]+|\'[^\']*\'|"[^"]*"))?'
)
attribute_no_lf = (
    r"[^\n\S]+[A-Za-z:_][A-Za-z0-9\-_\.:]*"
    r'(?:[^\n\S]*=[^\n\S]*(?:[^\s"\'`=<>]+|\'[^\n\']*\'|"[^\n"]*"))?'
)

whitespace = re.compile(r"\s+", flags=re.UNICODE)
uri = r"[A-Za-z][A-Za-z\-.+]{1,31}:[^\s<>]*?"
email = (
    r"[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
)


@functools.lru_cache(maxsize=128)
def is_punctuation(ch: str) -> bool:
    if ch in string.punctuation:
        return True
    category = unicodedata.category(ch)
    return category.startswith("P") or category.startswith("S")


_CODE_SPAN = re.compile(r"(`+)(?!`)([\s\S]+?)(?<!`)\1(?!`)")
_ESCAPE_OR_BACKTICKS = re.compile(r"\\[\s\S]|`+")


def find_code_spans(text: str) -> Iterator[re.Match[str]]:
    """Find the code spans of the text.

    A backslash escapes the backtick after it, so that one is not part of the run
    of backticks that opens a span. Inside a span the backslash is a plain
    character.
    """
    pos = 0
    while match := _ESCAPE_OR_BACKTICKS.search(text, pos):
        pos = match.end()
        if match.group()[0] != "\\":
            span = _CODE_SPAN.match(text, match.start())
            if span:
                yield span
                pos = span.end()
