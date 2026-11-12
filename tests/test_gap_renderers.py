"""Gap tests for Markdown/AST/XML/LaTeX renderers and the CLI.

Existing coverage: MarkdownRenderer round-trips for code fences, code spans,
link destinations, loose lists and link refs (test_basic); AST/XML basics
(test_basic); LaTeX documents for the main elements (test_latex). This file
covers renderer conversions the existing suites do not pin down, plus
renderer fallbacks and the latex+footnote failure mode.
"""

import pytest

import marko
from marko import Markdown
from marko.ast_renderer import ASTRenderer, XMLRenderer
from marko.ext.latex_renderer import LatexRenderer
from marko.md_renderer import MarkdownRenderer

MD = Markdown(renderer=MarkdownRenderer)
AST = Markdown(renderer=ASTRenderer)
XML = Markdown(renderer=XMLRenderer)
LATEX = Markdown(renderer=LatexRenderer)


def test_md_setext_headings_become_atx():
    assert MD("Title\n=====\n") == "# Title\n"
    assert MD("Title\n-----\n") == "## Title\n"


def test_md_thematic_break_always_renders_as_star_break():
    assert MD("***\n") == "* * *\n"


def test_md_quote_lazy_continuation_and_html_roundtrip():
    out = MD("> a\n> b\n")
    # The continuation line loses its "> " prefix in Markdown output, but
    # re-parsing still yields the same quote (lazy continuation).
    assert out == "> a\nb\n"
    assert marko.convert(out) == marko.convert("> a\n> b\n")


def test_md_ordered_list_start_is_preserved():
    assert MD("5. a\n6. b\n") == "5. a\n6. b\n"


def test_md_collapses_multiple_blank_lines():
    assert MD("a\n\n\nb\n") == "a\n\nb\n"


def test_md_hard_break_becomes_backslash_break():
    assert MD("a  \nb\n") == "a\\\nb\n"
    assert MD("a\\\nb\n") == "a\\\nb\n"


def test_md_link_and_image_edges():
    assert MD("[a]()\n") == "[a](<>)\n"
    assert MD("<https://example.com>\n") == "<https://example.com>\n"
    assert MD("# a *b* `c`\n") == "# a *b* `c`\n"
    assert MD('![alt](img.png "T")\n') == '![alt](img.png "T")\n'


def test_md_fenced_code_uses_tilde_when_info_has_backtick():
    assert MD("~~~a`b\ncode\n~~~\n") == "~~~a`b\ncode\n~~~\n"


def test_md_link_ref_is_preserved_but_image_ref_expands():
    assert MD("a [x][y]\n\n[y]: /u\n") == "a [x][y]\n\n[y]: /u\n"
    assert MD("![alt][r]\n\n[r]: /img\n") == "![alt](/img)\n\n[r]: /img\n"


def test_md_html_block_passthrough_adds_trailing_newline():
    assert MD("<div>\nx\n</div>\n") == "<div>\nx\n</div>\n\n"


def test_ast_document_keys_and_list_attributes():
    doc = AST("- a\n- b\n")
    assert set(doc.keys()) == {"children", "element", "link_ref_defs", "source_span"}
    lst = doc["children"][0]
    assert lst["element"] == "list"
    assert lst["bullet"] == "-"
    assert lst["ordered"] is False
    assert lst["start"] == 1
    assert lst["tight"] is True


def test_ast_link_spans_and_attributes():
    link = AST('[a](u "T")\n')["children"][0]["children"][0]
    assert link["element"] == "link"
    assert link["dest"] == "u"
    assert link["title"] == "T"
    assert link["dest_span"] == (4, 5)
    assert link["title_span"] == (6, 9)


def test_ast_raw_text_unescapes_and_code_block_flag():
    raw = AST("a &amp; b\n")["children"][0]["children"][0]
    assert raw["children"] == "a & b"
    assert raw["escape"] is True
    code = AST("    code\n")["children"][0]
    assert code["element"] == "code_block"
    assert code["lang"] == ""
    assert code["extra"] == ""
    assert code["children"][0]["escape"] is False
    assert code["children"][0]["children"] == "code\n"


def test_xml_empty_document_and_heading_structure():
    out = XML("")
    assert out.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert '<!DOCTYPE document SYSTEM "CommonMark.dtd">' in out
    assert '<document link_ref_defs="{}" source_span="(0, 0)" />' in out
    out = XML("# Hi\n")
    assert '<heading level="1"' in out
    assert "Hi" in out


def test_xml_link_attributes():
    out = XML("[a](u)\n")
    assert 'dest="u"' in out
    assert "<link " in out


def test_latex_strikethrough_falls_back_to_escaped_tildes():
    out = LATEX("a ~~b~~ c\n")
    assert "\\~{}\\~{}b\\~{}\\~{}" in out


def test_latex_table_falls_back_to_raw_lines():
    out = LATEX("| A |\n| --- |\n| 1 |\n")
    assert "| A |\n| --- |\n| 1 |" in out


def test_latex_packages_reset_between_documents():
    with_packages = LATEX("![a](x.png)\n")
    assert "\\usepackage{graphicx}" in with_packages
    plain = LATEX("para\n")
    assert "\\usepackage" not in plain


def test_latex_link_title_is_dropped_and_setext_maps_to_part():
    assert "\\href{u}{a}" in LATEX('[a](u "T")\n')
    assert "\\part*{Title}" in LATEX("Title\n=====\n")


def test_latex_code_span_escapes_and_nested_lists():
    assert "\\texttt{x\\_y\\$z}" in LATEX("a `x_y$z` b\n")
    out = LATEX("- a\n  - b\n")
    assert out.count("\\begin{itemize}") == 2


def test_latex_with_footnote_raises_not_implemented():
    # The LaTeX renderer has no footnote_ref render function and no
    # fallback for it, so rendering a footnote document raises.
    md = Markdown(renderer=LatexRenderer, extensions=["footnote"])
    with pytest.raises(NotImplementedError):
        md("a[^1]\n\n[^1]: one\n")
