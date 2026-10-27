"""Gap tests for the GFM extension.

Existing coverage (test_ext.py): GFM alerts (several types), one table-in-
list Markdown round-trip. This file covers table alignment/structure, the
strikethrough pattern edges, bare-URL trimming, task lists, and alert
fallbacks.
"""

import pytest

from marko import Markdown
from marko.ast_renderer import ASTRenderer
from marko.ext.gfm import GFM
from marko.md_renderer import MarkdownRenderer

HTML = Markdown(extensions=[GFM])
MD = Markdown(renderer=MarkdownRenderer, extensions=[GFM])
AST = Markdown(renderer=ASTRenderer, extensions=[GFM])


def test_table_alignments_propagate_to_body_cells():
    table = HTML.parse("| A | B |\n|:--- | ---: |\n| 1 | 2 |\n").children[0]
    assert table.num_of_cols == 2
    assert table.head.children[0].align == "left"
    assert [c.align for c in table.head.children] == ["left", "right"]
    assert [c.align for c in table.children[1].children] == ["left", "right"]


def test_table_center_alignment_and_no_alignment():
    out = HTML("| A | B |\n|:---: | --- |\n| 1 | 2 |\n")
    assert '<th align="center">A</th>' in out
    assert "<th>B</th>" in out
    assert '<td align="center">1</td>' in out
    assert "<td>2</td>" in out


def test_table_without_outer_pipes_parses():
    out = HTML("A | B\n--- | ---\n1 | 2\n")
    assert "<table>" in out and "<th>A</th>" in out


def test_table_with_short_delimiter_row_is_not_a_table():
    out = HTML("| A | B | C |\n| --- | --- |\n| 1 | 2 |\n")
    assert "<table>" not in out
    assert out.startswith("<p>")


def test_table_with_missing_delimiter_row_is_not_a_table():
    out = HTML("| A | B |\n| 1 | 2 |\n")
    assert "<table>" not in out


def test_extra_body_cells_are_truncated_to_header_count():
    out = HTML("| A |\n| --- |\n| 1 | 2 | 3 |\n")
    assert "<td>1</td>" in out
    assert "<td>2</td>" not in out
    assert "<td>3</td>" not in out


def test_table_cells_parse_inline_markup():
    out = HTML("| A | B |\n| --- | --- |\n| *x* | `y` |\n")
    assert "<td><em>x</em></td>" in out
    assert "<td><code>y</code></td>" in out


def test_table_markdown_roundtrip_keeps_alignment_markers():
    assert MD("| A | B |\n|:---: | --- |\n| 1 | 2 |\n") == (
        "| A | B |\n|:---: | --- |\n| 1 | 2 |\n"
    )


@pytest.mark.parametrize(
    "text, expected",
    [
        ("a ~~b~~ c\n", "<p>a <del>b</del> c</p>\n"),
        # A single tilde also deletes: the pattern is (~|~~), not just ~~.
        ("a ~b~ c\n", "<p>a <del>b</del> c</p>\n"),
        ("a ~ b ~ c\n", "<p>a <del> b </del> c</p>\n"),
        ("a ~b c\n", "<p>a ~b c</p>\n"),
        # Three tildes on each side do not match (lookarounds exclude ~).
        ("a ~~~b~~~ c\n", "<p>a ~~~b~~~ c</p>\n"),
    ],
)
def test_strikethrough_pattern_edges(text, expected):
    assert HTML(text) == expected


def test_strikethrough_markdown_and_ast_forms():
    assert MD("a ~~b~~ c\n") == "a ~~b~~ c\n"
    ast = AST("a ~~b~~ c\n")["children"][0]["children"]
    strike = ast[1]
    assert strike["element"] == "strikethrough"
    assert strike["children"][0]["children"] == "b"


def test_bare_url_trims_trailing_punctuation():
    assert HTML("https://example.com/a.\n") == (
        '<p><a href="https://example.com/a">https://example.com/a</a>.</p>\n'
    )
    assert HTML("see https://example.com/a, and www.example.com!\n") == (
        '<p>see <a href="https://example.com/a">https://example.com/a</a>, '
        'and <a href="http://www.example.com">www.example.com</a>!</p>\n'
    )


def test_bare_url_paren_balancing_and_www_prefix():
    assert HTML("(https://example.com/a)\n") == (
        '<p>(<a href="https://example.com/a">https://example.com/a</a>)</p>\n'
    )
    assert HTML("visit www.example.com/path\n") == (
        '<p>visit <a href="http://www.example.com/path">'
        "www.example.com/path</a></p>\n"
    )


def test_bare_url_email_and_mid_word_limits():
    assert HTML("mail me@example.com ok\n") == (
        '<p>mail <a href="mailto:me@example.com">me@example.com</a> ok</p>\n'
    )
    # A URL glued to a preceding word character is not autolinked.
    assert HTML("xhttps://example.com\n") == "<p>xhttps://example.com</p>\n"
    # A mailto: scheme prefix is not treated as a bare URL either.
    assert HTML("mailto:me@example.com\n") == "<p>mailto:me@example.com</p>\n"


@pytest.mark.parametrize(
    "text, checked, html_frag",
    [
        ("- [ ] todo\n", False, '<input disabled="" type="checkbox"> todo'),
        ("- [x] done\n", True, '<input checked="" disabled="" type="checkbox"> done'),
        ("- [X] done\n", True, '<input checked="" disabled="" type="checkbox"> done'),
        ("1. [x] done\n", True, '<input checked="" disabled="" type="checkbox"> done'),
    ],
)
def test_task_list_items(text, checked, html_frag):
    assert html_frag in HTML(text)
    paragraph = HTML.parse(text).children[0].children[0].children[0]
    assert paragraph.checked is checked


def test_non_task_bracket_stays_literal():
    assert HTML("- [y] not task\n") == "<ul>\n<li>[y] not task</li>\n</ul>\n"


@pytest.mark.parametrize("alert", ["NOTE", "IMPORTANT", "note"])
def test_alert_types_and_case_insensitivity(alert):
    out = HTML(f"> [!{alert}]\n> hi\n")
    assert f'class="alert alert-{alert.lower()}"' in out
    assert f"<p>{alert.title() if alert.isupper() else 'Note'}</p>" in out


def test_unknown_alert_is_plain_blockquote():
    out = HTML("> [!FOO]\n> hi\n")
    assert out.startswith("<blockquote>\n<p>[!FOO]")
    assert "alert" not in out


def test_alert_markdown_roundtrip_and_ast_type():
    assert MD("> [!NOTE]\n> hi\n") == "> [!NOTE]\n> hi\n"
    ast = AST("> [!NOTE]\n> hi\n")["children"][0]
    assert ast["element"] == "alert"
    assert ast["alert_type"] == "NOTE"
