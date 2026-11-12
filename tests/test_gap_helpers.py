"""Gap tests for marko.helpers (not covered by tests/test_helpers.py).

Existing coverage: is_paired (default parens), partition_by_spaces (default
spaces), load_extension, Source no-state errors. This file covers the rest of
the public helpers: camel_to_snake_case, normalize_label, find_next, custom
delimiters/spaces, and MarkoExtension defaults.
"""

import pytest

from marko.helpers import (
    MarkoExtension,
    camel_to_snake_case,
    find_next,
    is_paired,
    normalize_label,
    partition_by_spaces,
)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Heading", "heading"),
        ("StrongEmphasis", "strong_emphasis"),
        ("HTMLBlock", "html_block"),
        ("LinkRefDef", "link_ref_def"),
        ("ABC", "abc"),
        ("MyHTTPServer", "my_http_server"),
        ("ABcDef", "a_bc_def"),
    ],
)
def test_camel_to_snake_case(name, expected):
    assert camel_to_snake_case(name) == expected


def test_camel_to_snake_case_lowercase_only_is_empty():
    # No uppercase run matches, so the join yields an empty string.
    assert camel_to_snake_case("a") == ""
    assert camel_to_snake_case("") == ""


@pytest.mark.parametrize(
    "label, expected",
    [
        ("  Foo   Bar ", "foo bar"),
        ("FOO\tBAR", "foo bar"),
        ("a\nb", "a b"),
        ("  ", ""),
        ("MixedCASE", "mixedcase"),
    ],
)
def test_normalize_label(label, expected):
    assert normalize_label(label) == expected


def test_find_next_basic_and_start_end():
    assert find_next("a,b;c", ",;") == 1
    assert find_next("a,b,c", ",", start=2) == 3
    assert find_next("a,b,c", ",", start=2, end=3) == -1


def test_find_next_skips_backslash_escaped_targets():
    assert find_next(r"a\,b,c", ",") == 4
    # A trailing backslash escapes nothing and yields no match.
    assert find_next("ab\\", ",") == -1


def test_find_next_disallowed_returns_minus_two():
    assert find_next("a!b,c", ",", disallowed="!") == -2
    # A target found before any disallowed character still wins.
    assert find_next("a,b!c", ",", disallowed="!") == 1
    assert find_next("abc", ",") == -1


@pytest.mark.parametrize(
    "text, expected",
    [
        ("[a[b]]", True),
        ("[a[b]", False),
        (r"[a\]b]", True),
        ("{a{b}c}", True),
    ],
)
def test_is_paired_custom_delimiters(text, expected):
    if text.startswith("["):
        result = is_paired(text, "[", "]")
    else:
        result = is_paired(text, "{", "}")
    assert result == expected


@pytest.mark.parametrize(
    "text, spaces, expected",
    [
        ("a:b:c", ":", ("a", ":", "b:c")),
        ("  hello", " \t", ("", "  ", "hello")),
        ("hello   ", " \t", ("hello", "   ", "")),
        ("nodelim", " \t", ("nodelim", "", "")),
        ("a\t\tb", " \t", ("a", "\t\t", "b")),
    ],
)
def test_partition_by_spaces_variants(text, spaces, expected):
    assert partition_by_spaces(text, spaces=spaces) == expected


def test_marko_extension_defaults_are_empty_and_independent():
    first = MarkoExtension()
    second = MarkoExtension()
    assert first.parser_mixins == []
    assert first.renderer_mixins == []
    assert first.elements == []
    first.parser_mixins.append(object())
    assert second.parser_mixins == []
