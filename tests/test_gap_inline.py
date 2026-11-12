"""Gap tests for inline parsing boundaries.

Spec fixtures cover the standard emphasis/link/code cases; this file targets
edges the fixtures do not pin down: entity handling, backslash quirks, break
kinds, autolink limits, nested emphasis, code-span space stripping, and
link-reference resolution rules.
"""

import pytest

import marko
from marko import inline


def test_unknown_entity_is_escaped_but_known_ones_resolve():
    assert marko.convert("&nosuchentity;\n") == "<p>&amp;nosuchentity;</p>\n"
    assert marko.convert("&#65;&#x42;\n") == "<p>AB</p>\n"


def test_backslash_before_non_punctuation_keeps_backslash():
    assert marko.convert("\\a \\* \\#\n") == "<p>\\a * #</p>\n"


def test_backslash_newline_is_hard_break():
    assert marko.convert("a\\\nb\n") == "<p>a<br />\nb</p>\n"


def test_soft_and_hard_breaks():
    assert marko.convert("a\nb\n") == "<p>a\nb</p>\n"
    assert marko.convert("a  \nb\n") == "<p>a<br />\nb</p>\n"


def test_autolink_email_and_www_in_angle_brackets():
    assert marko.convert("<a@b.com>\n") == '<p><a href="mailto:a@b.com">a@b.com</a></p>\n'
    # www. inside angle brackets is not an autolink.
    assert marko.convert("<www.example.com>\n") == "<p>&lt;www.example.com&gt;</p>\n"


def test_inline_html_passes_through():
    assert marko.convert("a <b>c</b> d\n") == "<p>a <b>c</b> d</p>\n"


def test_nested_emphasis_and_link_with_formatted_text():
    assert (
        marko.convert("***a*** and **a *b* c**\n")
        == "<p><em><strong>a</strong></em> and <strong>a <em>b</em> c</strong></p>\n"
    )
    assert (
        marko.convert("[*a* **b**](u)\n")
        == '<p><a href="u"><em>a</em> <strong>b</strong></a></p>\n'
    )


def test_code_span_with_inner_backtick_and_space_stripping():
    assert marko.convert("``a ` b``\n") == "<p><code>a ` b</code></p>\n"
    # One space is stripped from each side when both sides are padded.
    assert marko.convert("`  a  `\n") == "<p><code> a </code></p>\n"


def test_literal_strip_backslash():
    assert inline.Literal.strip_backslash("\\*") == "*"
    assert inline.Literal.strip_backslash("\\a") == "\\a"


def test_link_reference_case_insensitive_and_first_def_wins():
    assert marko.convert("[a][FOO]\n\n[foo]: /u\n") == '<p><a href="/u">a</a></p>\n'
    assert (
        marko.convert("[a][x]\n\n[x]: /first\n[x]: /second\n")
        == '<p><a href="/first">a</a></p>\n'
    )


def test_shortcut_and_collapsed_reference_links():
    assert marko.convert("[foo]\n\n[foo]: /u\n") == '<p><a href="/u">foo</a></p>\n'
    assert marko.convert("[foo][]\n\n[foo]: /u\n") == '<p><a href="/u">foo</a></p>\n'


def test_setext_headings_beat_thematic_break_lookalikes():
    assert marko.convert("foo\n---\n") == "<h2>foo</h2>\n"
    assert marko.convert("foo\n===\n") == "<h1>foo</h1>\n"


@pytest.mark.parametrize(
    "text, expected",
    [
        ("> a\nb\n", "<blockquote>\n<p>a\nb</p>\n</blockquote>\n"),
        ("> > a\n", "<blockquote>\n<blockquote>\n<p>a</p>\n</blockquote>\n</blockquote>\n"),
    ],
)
def test_blockquote_lazy_and_nested(text, expected):
    assert marko.convert(text) == expected
