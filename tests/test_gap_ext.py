"""Gap tests for footnote, TOC and pangu extensions.

Existing coverage (test_ext.py): one basic footnote, footnote label escapes,
basic TOC render/maxdepth/replace-tags, one pangu case plus Chinese
punctuation. This file covers footnote numbering order, TOC depth/reset/
custom format, and pangu boundary rules.
"""

import pytest

from marko import Markdown
from marko.ext.toc import make_extension as make_toc
from marko.md_renderer import MarkdownRenderer

FN = Markdown(extensions=["footnote"])
TOC = Markdown(extensions=["toc"])
PANGU = Markdown(extensions=["pangu"])


def test_footnote_two_defs_need_blank_line_separation():
    out = FN("a[^1] b[^2]\n\n[^1]: one\n\n[^2]: two\n")
    assert 'id="fnref-1"' in out and 'id="fnref-2"' in out
    assert out.index('id="fn-1"') < out.index('id="fn-2"')


def test_footnote_display_numbers_follow_first_reference_order():
    # The display number follows reference order, while the id follows the
    # label: first-referenced [^2] is numbered 1 but keeps id fn-2.
    out = FN("b[^2] a[^1]\n\n[^1]: one\n\n[^2]: two\n")
    assert 'id="fnref-2"><a href="#fn-2">1</a>' in out
    assert 'id="fnref-1"><a href="#fn-1">2</a>' in out
    assert out.index('id="fn-2"') < out.index('id="fn-1"')


def test_footnote_duplicate_reference_shares_id():
    out = FN("a[^1] b[^1]\n\n[^1]: one\n")
    assert out.count('id="fnref-1"') == 2


def test_footnote_undefined_reference_stays_literal():
    out = FN("a[^9]\n")
    assert out == "<p>a[^9]</p>\n"
    assert "footnotes" not in out


def test_footnote_indented_continuation_joins_def():
    out = FN("a[^1]\n\n[^1]: line1\n    cont\n")
    assert "line1\ncont" in out


def test_footnote_markdown_roundtrip():
    md = Markdown(renderer=MarkdownRenderer, extensions=["footnote"])
    assert md("a[^1]\n\n[^1]: one\n") == "a[^1]\n\n[^1]: one\n"


def test_toc_empty_document_renders_empty():
    md = Markdown(extensions=["toc"])
    md("para\n")
    assert md.renderer.render_toc() == ""


def test_toc_maxdepth_limits_nesting():
    md = Markdown(extensions=["toc"])
    md("# A\n## B\n### C\n#### D\n")
    default = md.renderer.render_toc()
    assert "#d" not in default and "#c" in default
    assert "#b" not in md.renderer.render_toc(maxdepth=1)
    assert "#d" in md.renderer.render_toc(maxdepth=10)


def test_toc_keeps_inline_formatting_in_text_but_plain_slug():
    md = Markdown(extensions=["toc"])
    md("# Hello *World*\n")
    toc = md.renderer.render_toc()
    assert '<a href="#hello-world">Hello <em>World</em></a>' in toc


def test_toc_duplicate_headings_produce_duplicate_slugs():
    md = Markdown(extensions=["toc"])
    md("# Foo\n# Foo\n")
    assert md.renderer.render_toc().count('href="#foo"') == 2


def test_toc_resets_between_renders():
    md = Markdown(extensions=["toc"])
    md("# One\n")
    assert "#one" in md.renderer.render_toc()
    md("# Two\n")
    toc = md.renderer.render_toc()
    assert "#two" in toc and "#one" not in toc


def test_toc_custom_item_format():
    md = Markdown(extensions=[make_toc(item_format='<li data-slug="{slug}">{text}</li>')])
    md("# Hi There\n")
    assert '<li data-slug="hi-there">Hi There</li>' in md.renderer.render_toc()


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "中文English混合\n",
            '<p>中文<span class="pangu"></span>English<span class="pangu"></span>混合</p>\n',
        ),
        (
            "中文123English\n",
            # Digits and Latin letters are one class, so only the CJK->digit
            # boundary gets a span, not the digit->Latin boundary.
            '<p>中文<span class="pangu"></span>123English</p>\n',
        ),
        ("a中文b\n", '<p>a<span class="pangu"></span>中文<span class="pangu"></span>b</p>\n'),
    ],
)
def test_pangu_boundaries(text, expected):
    assert PANGU(text) == expected


def test_pangu_fullwidth_punctuation_blocks_the_boundary():
    # A fullwidth comma is neither CJK-letter nor Latin, so no span appears.
    assert PANGU("中文，English\n") == "<p>中文，English</p>\n"


def test_pangu_skips_code_spans_but_applies_in_link_text():
    assert PANGU("`中文English`\n") == "<p><code>中文English</code></p>\n"
    assert PANGU("[中文English](u)\n") == (
        '<p><a href="u">中文<span class="pangu"></span>English</a></p>\n'
    )
