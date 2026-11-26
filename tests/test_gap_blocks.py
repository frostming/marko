"""Gap tests for block-level structure and element attributes."""

import pytest

import marko
from marko import Markdown


def test_changing_bullet_starts_a_new_list():
    out = marko.convert("- a\n* b\n")
    assert out.count("<ul>") == 2
    out = marko.convert("1. a\n2. b\n\n- c\n")
    assert "<ol>" in out and "<ul>" in out


def test_paren_ordered_list_attributes():
    lst = Markdown().parse("3) a\n4) b\n").children[0]
    assert lst.ordered is True
    assert lst.start == 3
    assert lst.bullet == "3)"


def test_unordered_list_attributes_and_tight_flag():
    lst = Markdown().parse("- a\n- b\n").children[0]
    assert lst.ordered is False
    assert lst.start == 1
    assert lst.bullet == "-"
    assert lst.tight is True


def test_loose_list_is_not_tight():
    lst = Markdown().parse("1. a\n\n2. b\n").children[0]
    assert lst.tight is False


def test_indented_code_inside_list_item():
    out = marko.convert("- a\n\n      code\n")
    assert "<pre><code>code\n</code></pre>" in out


def test_fenced_code_lang_and_extra():
    code = Markdown().parse("```python extra info\ncode\n```\n").children[0]
    assert code.lang == "python"
    assert code.extra == "extra info"
    assert code.children[0].children == "code\n"


def test_tilde_fence_and_empty_language():
    code = Markdown().parse("~~~ruby\ncode\n~~~\n").children[0]
    assert code.lang == "ruby"
    assert code.extra == ""
    assert Markdown().parse("```\nx\n```\n").children[0].lang == ""


def test_heading_and_setext_levels():
    assert Markdown().parse("# H\n").children[0].level == 1
    setext = Markdown().parse("Title\n---\n").children[0]
    assert type(setext).__name__ == "SetextHeading"
    assert setext.level == 2


def test_thematic_break_after_list():
    assert marko.convert("- a\n\n---\n") == "<ul>\n<li>a</li>\n</ul>\n<hr />\n"


def test_html_comment_block():
    assert marko.convert("<!-- c -->\n\npara\n") == "<!-- c -->\n<p>para</p>\n"


def test_link_ref_defs_normalized_keys():
    doc = Markdown().parse('[a][X]\n\n[X]: /u "T"\n')
    assert list(doc.link_ref_defs.keys()) == ["x"]
    assert doc.link_ref_defs["x"] == ("/u", '"T"')


def test_element_get_type_forms():
    paragraph = Markdown().parse("hi\n").children[0]
    assert paragraph.get_type() == "Paragraph"
    assert paragraph.get_type(snake_case=True) == "paragraph"


def test_document_repr_mentions_element_names():
    assert "StrongEmphasis" in repr(Markdown().parse("**x**\n"))


def test_parser_registers_standard_block_elements():
    from marko.parser import Parser

    keys = Parser().block_elements.keys()
    for name in ("Heading", "FencedCode", "List", "Quote", "LinkRefDef"):
        assert name in keys
