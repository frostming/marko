"""Tests for source mapping info (see issue #273)."""

from __future__ import annotations

import re

from marko import Markdown, MarkoExtension, block, inline
from marko.element import _SourceMap
from marko.ext.gfm import gfm
from marko.parser import Parser
from marko.source import Source


def _span_text(text: str, span) -> str:
    """Return the slice of ``text`` covered by a (start, end) span."""
    assert span is not None
    return text[span[0] : span[1]]


class TestBlockSpans:
    def test_document_and_paragraph(self):
        text = "Hello world\n"
        doc = Markdown().parse(text)
        assert doc.source_span == (0, len(text))
        para = doc.children[0]
        assert isinstance(para, block.Paragraph)
        assert para.source_span == (0, len(text))
        assert para.start_pos == 0
        assert para.end_pos == len(text)

    def test_heading(self):
        text = "### Title ###\n"
        doc = Markdown().parse(text)
        heading = doc.children[0]
        assert isinstance(heading, block.Heading)
        assert heading.source_span == (0, len(text))
        # the inline body is the content between the hashes
        child = heading.children[0]
        assert child.source_span == (4, 9)
        assert _span_text(text, child.source_span) == "Title"

    def test_setext_heading(self):
        text = "Title\n===\n"
        doc = Markdown().parse(text)
        heading = doc.children[0]
        assert isinstance(heading, block.SetextHeading)
        assert heading.source_span == (0, len(text))
        child = heading.children[0]
        assert _span_text(text, child.source_span) == "Title"

    def test_fenced_code(self):
        text = "```python\nprint(1)\n```\n"
        doc = Markdown().parse(text)
        code = doc.children[0]
        assert isinstance(code, block.FencedCode)
        assert code.source_span == (0, len(text))

    def test_list_items(self):
        text = "- item1\n- item2\n"
        doc = Markdown().parse(text)
        lst = doc.children[0]
        assert isinstance(lst, block.List)
        assert lst.source_span == (0, len(text))
        item1, item2 = lst.children
        assert _span_text(text, item1.source_span) == "- item1\n"
        assert _span_text(text, item2.source_span) == "- item2\n"
        para1 = item1.children[0]
        assert isinstance(para1, block.Paragraph)
        assert para1.source_span == (2, 8)
        assert _span_text(text, para1.children[0].source_span) == "item1"

    def test_quote(self):
        text = "> hello\n> world\n"
        doc = Markdown().parse(text)
        quote = doc.children[0]
        assert isinstance(quote, block.Quote)
        assert quote.source_span == (0, len(text))
        para = quote.children[0]
        # the paragraph covers the content, quote markers belong to the quote
        assert para.source_span[0] == 2
        assert _span_text(text, para.children[0].source_span) == "hello"
        assert _span_text(text, para.children[-1].source_span) == "world"

    def test_nested_list_items_exclude_quote_markers(self):
        text = "> - one\n> - two\n"
        quote = Markdown().parse(text).children[0]
        item1, item2 = quote.children[0].children
        assert _span_text(text, item1.source_span) == "- one\n"
        assert _span_text(text, item2.source_span) == "- two\n"

    def test_nested_code_block_excludes_quote_marker(self):
        text = ">     code\n"
        code = Markdown().parse(text).children[0].children[0]
        assert isinstance(code, block.CodeBlock)
        assert _span_text(text, code.source_span) == "    code\n"


class TestInlineSpans:
    def test_link_issue_example(self):
        """The exact example from issue #273."""
        text = "[Google](https://google.com)\n"
        doc = Markdown().parse(text)
        link = doc.children[0].children[0]
        assert isinstance(link, inline.Link)
        assert link.source_span == (0, 28)
        # content: the link text
        assert _span_text(text, link.children[0].source_span) == "Google"
        # syntax: the brackets and the parentheses
        assert [_span_text(text, s) for s in link.syntax_spans] == [
            "[",
            "](https://google.com)",
        ]
        # the destination is exposed separately
        assert link.dest_span == (9, 27)
        assert _span_text(text, link.dest_span) == "https://google.com"
        assert link.title_span is None

    def test_link_with_title(self):
        text = '[a](url "title")\n'
        doc = Markdown().parse(text)
        link = doc.children[0].children[0]
        assert link.dest_span == (4, 7)
        assert _span_text(text, link.dest_span) == "url"
        assert link.title_span == (8, 15)
        assert _span_text(text, link.title_span) == '"title"'

    def test_reference_link(self):
        text = "[foo][bar]\n\n[bar]: /url\n"
        doc = Markdown().parse(text)
        link = doc.children[0].children[0]
        assert isinstance(link, inline.Link)
        assert link.source_span == (0, 10)
        # the destination is not in the source at this position
        assert link.dest_span is None
        assert link.title_span is None
        assert _span_text(text, link.children[0].source_span) == "foo"

    def test_image(self):
        text = "![alt](img.png)\n"
        doc = Markdown().parse(text)
        image = doc.children[0].children[0]
        assert isinstance(image, inline.Image)
        assert _span_text(text, image.children[0].source_span) == "alt"
        assert _span_text(text, image.dest_span) == "img.png"

    def test_emphasis_syntax_spans(self):
        text = "**bold** and *em*\n"
        doc = Markdown().parse(text)
        children = doc.children[0].children
        strong = children[0]
        assert isinstance(strong, inline.StrongEmphasis)
        assert [_span_text(text, s) for s in strong.syntax_spans] == ["**", "**"]
        assert _span_text(text, strong.children[0].source_span) == "bold"
        em = children[2]
        assert isinstance(em, inline.Emphasis)
        assert [_span_text(text, s) for s in em.syntax_spans] == ["*", "*"]

    def test_code_span(self):
        text = "`code`\n"
        doc = Markdown().parse(text)
        code = doc.children[0].children[0]
        assert isinstance(code, inline.CodeSpan)
        assert [_span_text(text, s) for s in code.syntax_spans] == ["`", "`"]

    def test_literal_escape(self):
        text = r"\*not em\*" + "\n"
        doc = Markdown().parse(text)
        children = doc.children[0].children
        lit = children[0]
        assert isinstance(lit, inline.Literal)
        assert _span_text(text, lit.source_span) == r"\*"
        assert _span_text(text, lit.syntax_spans[0]) == "\\"

    def test_autolink(self):
        text = "<http://example.org>\n"
        doc = Markdown().parse(text)
        link = doc.children[0].children[0]
        assert isinstance(link, inline.AutoLink)
        assert [_span_text(text, s) for s in link.syntax_spans] == ["<", ">"]
        assert _span_text(text, link.children[0].source_span) == "http://example.org"

    def test_line_break(self):
        text = "a  \nb\n"
        doc = Markdown().parse(text)
        children = doc.children[0].children
        br = children[1]
        assert isinstance(br, inline.LineBreak)
        assert not br.soft
        assert _span_text(text, br.source_span) == "  \n"
        assert _span_text(text, br.syntax_spans[0]) == "  "

    def test_multiline_paragraph_with_indentation(self):
        text = "  hello\n  world\n"
        doc = Markdown().parse(text)
        para = doc.children[0]
        assert isinstance(para, block.Paragraph)
        assert para.source_span == (0, len(text))
        raw1, br, raw2 = para.children
        assert _span_text(text, raw1.source_span) == "hello"
        assert _span_text(text, br.source_span) == "\n"
        assert _span_text(text, raw2.source_span) == "world"

    def test_inline_positions_are_contiguous_cover(self):
        """The children spans should exactly tile the inline body region."""
        text = "Hello *world* and `code`\n"
        doc = Markdown().parse(text)
        para = doc.children[0]
        spans = [c.source_span for c in para.children]
        assert spans[0][0] == 0
        assert spans[-1][1] == len(text) - 1
        for prev, cur in zip(spans, spans[1:]):
            assert prev[1] == cur[0]


class TestGFMSpans:
    def test_bare_url_has_no_syntax_spans(self):
        text = "https://example.com/path\n"
        url = gfm.parse(text).children[0].children[0]
        assert url.syntax_spans is None
        assert _span_text(text, url.children[0].source_span) == text.rstrip()

    def test_table_cells(self):
        text = "| Item | Price |\n| ---- | ----- |\n| Apple | $1 |\n"
        doc = gfm.parse(text)
        table = doc.children[0]
        assert isinstance(table, block.BlockElement)
        # the table covers all rows including the delimiter row
        assert _span_text(text, table.source_span) == text
        head, body = table.children
        assert _span_text(text, head.source_span) == "| Item | Price |\n"
        for cell, expected in zip(head.children, ["Item", "Price"]):
            assert _span_text(text, cell.source_span) == expected
            child = cell.children[0]
            assert _span_text(text, child.source_span) == expected
        assert _span_text(text, body.source_span) == "| Apple | $1 |\n"
        for cell, expected in zip(body.children, ["Apple", "$1"]):
            child = cell.children[0]
            assert _span_text(text, child.source_span) == expected

    def test_table_cell_escaped_pipe(self):
        text = "| a\\|b | c |\n| --- | --- |\n| 1 | 2 |\n"
        doc = gfm.parse(text)
        table = doc.children[0]
        cell = table.children[0].children[0]
        child = cell.children[0]
        # the inline body unescapes the pipe, but the span covers the source
        assert _span_text(text, child.source_span) == "a\\|b"

    def test_task_list_item(self):
        text = "- [x] Shopping\n"
        doc = gfm.parse(text)
        lst = doc.children[0]
        para = lst.children[0].children[0]
        assert para.checked is True
        child = para.children[0]
        # the checkbox is stripped from the inline body, only the rest remains
        assert _span_text(text, child.source_span) == " Shopping"

    def test_nested_quote_table(self):
        text = "> | a | b |\n> | - | - |\n> | 1 | 2 |\n"
        doc = gfm.parse(text)
        table = doc.children[0].children[0]
        assert table.source_span[0] == 2
        assert _span_text(text, table.source_span).startswith("| a | b |")
        body = table.children[-1]
        assert _span_text(text, body.children[0].children[0].source_span) == "1"
        assert _span_text(text, body.children[1].children[0].source_span) == "2"


class TestEdgeCases:
    def test_extension_inline_syntax_spans_are_none_without_positions(self):
        class CustomBlock(block.BlockElement):
            pattern = re.compile(r"@(.*)$", re.M)

            def __init__(self, match: re.Match[str]) -> None:
                self.inline_body = match.group(1)

            @classmethod
            def match(cls, source: Source) -> re.Match[str] | None:
                return source.expect_re(cls.pattern)

            @classmethod
            def parse(cls, source: Source) -> re.Match[str] | None:
                match = source.match
                source.consume()
                return match

        markdown = Markdown(extensions=[MarkoExtension(elements=[CustomBlock])])
        emphasis = markdown.parse("@**text**\n").children[0].children[0]
        assert isinstance(emphasis, inline.StrongEmphasis)
        assert emphasis.source_span is None
        assert emphasis.syntax_spans is None

    def test_unicode_leading_whitespace(self):
        text = "\u00a0hello\n"
        child = Markdown().parse(text).children[0].children[0]
        assert child.source_span == (1, 6)
        assert _span_text(text, child.source_span) == "hello"

    def test_crlf_normalized_positions(self):
        # Positions refer to the normalized source text
        doc = Markdown().parse("a\r\nb\r\n")
        para = doc.children[0]
        raw1 = para.children[0]
        assert _span_text("a\r\nb\r\n", raw1.source_span) == "a"

    def test_empty_document(self):
        doc = Markdown().parse("")
        assert doc.source_span == (0, 0)

    def test_start_pos_end_pos_properties(self):
        text = "abc\n"
        doc = Markdown().parse(text)
        para = doc.children[0]
        assert para.start_pos == 0
        assert para.end_pos == 4
        child = para.children[0]
        assert child.start_pos == 0
        assert child.end_pos == 3

    def test_repr_does_not_break(self):
        doc = Markdown().parse("**x**\n")
        assert "StrongEmphasis" in repr(doc)

    def test_paragraph_override_keeps_legacy_constructor(self):
        class Paragraph(block.Paragraph):
            override = True

            def __init__(self, lines):
                super().__init__(lines)

        parser = Parser()
        parser.add_element(Paragraph)
        para = parser.parse("hello\n").children[0]
        assert _span_text("hello\n", para.children[0].source_span) == "hello"

    def test_setext_override_keeps_legacy_constructor(self):
        class SetextHeading(block.SetextHeading):
            override = True

            def __init__(self, lines):
                super().__init__(lines)

        parser = Parser()
        parser.add_element(SetextHeading)
        heading = parser.parse("hello\n---\n").children[0]
        assert isinstance(heading, SetextHeading)
        assert _span_text("hello\n---\n", heading.children[0].source_span) == "hello"

    def test_source_map_compacts_contiguous_positions(self):
        positions = _SourceMap([(10, 1_000_000)])
        assert len(positions) == 1_000_000
        assert positions[0] == 10
        assert positions[-1] == 1_000_009
        assert len(positions._runs) == 1
