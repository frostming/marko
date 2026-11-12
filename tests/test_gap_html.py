"""Gap tests for the HTML renderer and the top-level Markdown API.

The CommonMark spec fixtures (test_spec.py) cover plain conversions; this
file targets renderer-specific behavior: URL/HTML escaping, list start
numbers, tight vs loose lists, image alt handling, and API validation.
"""

import pytest

import marko
from marko import Markdown
from marko.html_renderer import HTMLRenderer
from marko.parser import Parser
from marko.renderer import Renderer


@pytest.mark.parametrize(
    "url, expected",
    [
        ("javascript:alert(1)", "#harmful-link"),
        ("JaVaScRiPt:alert(1)", "#harmful-link"),
        ("vbscript:x", "#harmful-link"),
        ("data:text/html,x", "#harmful-link"),
        ("data:image/png;base64,xx", "#harmful-link"),
        ("https://example.com/a b", "https://example.com/a%20b"),
        ("https://example.com/?a=1&b=2", "https://example.com/?a=1&amp;b=2"),
        ("mailto:a@b.com", "mailto:a@b.com"),
    ],
)
def test_escape_url(url, expected):
    assert HTMLRenderer.escape_url(url) == expected


def test_escape_url_leading_whitespace_quirk():
    # The harmful-protocol check runs after quoting, so leading spaces are
    # percent-encoded first and the javascript: check no longer matches.
    assert HTMLRenderer.escape_url("  javascript:x") == "%20%20javascript:x"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("<a>&amp;&#42;&#x27;", "&lt;a&gt;&amp;*'"),
        ("a'b", "a'b"),
        ("&copy;", "\u00a9"),
        ("&nosuchentity;", "&amp;nosuchentity;"),
    ],
)
def test_escape_html_unescapes_then_escapes(raw, expected):
    assert HTMLRenderer.escape_html(raw) == expected


def test_ordered_list_start_attribute():
    assert '<ol start="3">' in marko.convert("3. a\n4. b\n")
    assert '<ol start="0">' in marko.convert("0. a\n1. b\n")
    assert '<ol start="999999999">' in marko.convert("999999999. a\n")
    assert "<ol>" in marko.convert("1. a\n2. b\n")


def test_tight_list_items_have_no_paragraph():
    out = marko.convert("- a\n- b\n")
    assert out == "<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n"


def test_loose_list_items_wrap_paragraphs():
    out = marko.convert("- a\n\n- b\n")
    assert "<li>\n<p>a</p>\n</li>" in out
    assert "<li>\n<p>b</p>\n</li>" in out


def test_image_alt_strips_inline_formatting():
    out = marko.convert("![*alt*](x.png)\n")
    assert '<img src="x.png" alt="alt" />' in out


def test_image_title_and_link_title_escaping():
    assert 'title="T"' in marko.convert('![alt](x.png "T")\n')
    assert 'title="t&quot;x"' in marko.convert('[a](u "t\\"x")\n')


def test_fenced_code_language_is_html_escaped():
    out = marko.convert("```a<b\nx\n```\n")
    assert 'class="language-a&lt;b"' in out


def test_indented_code_block_has_no_language_class():
    assert marko.convert("    x\n") == "<pre><code>x\n</code></pre>\n"


@pytest.mark.parametrize("text", ["***\n", "___\n", "- - -\n"])
def test_thematic_break_variants(text):
    assert marko.convert(text) == "<hr />\n"


def test_html_block_is_passed_through_unsanitized():
    assert marko.convert("<script>alert(1)</script>\n") == "<script>alert(1)</script>\n"


def test_empty_and_blank_documents_render_empty():
    assert marko.convert("") == ""
    assert marko.convert("\n\n") == ""


def test_empty_heading_and_seven_hashes():
    assert marko.convert("#\n") == "<h1></h1>\n"
    assert marko.convert("####### a\n") == "<p>####### a</p>\n"


def test_heading_closing_hashes_are_stripped():
    assert marko.convert("## a ##\n") == "<h2>a</h2>\n"


def test_link_ref_def_renders_nothing_extra():
    assert marko.convert("[a][x]\n\n[x]: /u\n") == '<p><a href="/u">a</a></p>\n'


def test_markdown_rejects_bad_parser_and_renderer():
    with pytest.raises(TypeError, match="parser must be a subclass of Parser"):
        Markdown(parser=object)
    with pytest.raises(TypeError, match="renderer must be a subclass of Renderer"):
        Markdown(renderer=object)


def test_markdown_setup_is_idempotent():
    md = Markdown()
    assert md.parse("hi\n").children[0].children[0].children == "hi"
    assert md.convert("hi\n") == "<p>hi</p>\n"


def test_module_level_parse_and_render():
    doc = marko.parse("hi\n")
    assert type(doc).__name__ == "Document"
    assert marko.render(doc) == "<p>hi</p>\n"
    assert isinstance(Parser, type)
    assert isinstance(Renderer, type)
