import re
from typing import Container, Iterable


def camel_to_snake_case(name: str) -> str:
    """Takes a camelCased string and converts to snake_case."""
    pattern = r"[A-Z][a-z]+|[A-Z]+(?![a-z])"
    return "_".join(map(str.lower, re.findall(pattern, name)))


def is_paired(text: Iterable[str], open: str = "(", close: str = ")") -> bool:
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


def normalize_label(label: str) -> str:
    """Return the normalized form of link label."""
    return re.sub(r"\s+", " ", label).strip().casefold()


def find_next(
    text: str,
    target: Container[str],
    start: int = 0,
    end: int | None = None,
    disallowed: Container[str] = (),
) -> int:
    """Find the next occurrence of target in text, and return the index
    Characters are escaped by backslash.
    Optional disallowed characters can be specified, if found, the search
    will fail with -2 returned. Otherwise, -1 is returned if not found.
    """
    if end is None:
        end = len(text)
    i = start
    escaped = False
    while i < end:
        c = text[i]
        if escaped:
            escaped = False
        elif c in target:
            return i
        elif c in disallowed:
            return -2
        elif c == "\\":
            escaped = True
        i += 1
    return -1


def partition_by_spaces(text: str, spaces: str = " \t") -> tuple[str, str, str]:
    """Split the given text by spaces or tabs, and return a tuple of
    (start, delimiter, remaining). If spaces are not found, the latter
    two elements will be empty.
    """
    start = end = -1
    for i, c in enumerate(text):
        if c in spaces:
            if start >= 0:
                continue
            start = i
        elif start >= 0:
            end = i
            break
    if start < 0:
        return text, "", ""
    if end < 0:
        return text[:start], text[start:], ""
    return text[:start], text[start:end], text[end:]
