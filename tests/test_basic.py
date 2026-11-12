from __future__ import annotations

import html
import re
import textwrap
import time

import pytest

import marko
from marko import block
from marko.ast_renderer import ASTRenderer, XMLRenderer
from marko.md_renderer import MarkdownRenderer
from marko.source import Source
from tests.normalize import normalize_html


class TestBasic:
    @pytest.mark.parametrize(
        "line", ["[l{i}]: /u{i}\n", "- [l{i}]: /u{i}\n", "> [l{i}]: /u{i}\n"]
    )
    def test_link_ref_def_run_scales_linearly(self, line):
        def best_of_three(text):
            best = float("inf")
            for _ in range(3):
                start = time.perf_counter()
                marko.convert(text)
                best = min(best, time.perf_counter() - start)
            return best

        small = "".join(line.format(i=i) for i in range(1000))
        large = "".join(line.format(i=i) for i in range(4000))
        ratio = best_of_three(large) / best_of_three(small)
        assert ratio < 8, f"4x the lines took {ratio:.1f}x the time"

    @pytest.mark.parametrize("opener", ["[a](", "![alt](", "[a]["])
    def test_unclosed_inline_link_openers_scale_linearly(self, opener):
        def best_of_three(text):
            best = float("inf")
            for _ in range(3):
                start = time.perf_counter()
                marko.convert(text)
                best = min(best, time.perf_counter() - start)
            return best

        ratio = best_of_three(opener * 8000) / best_of_three(opener * 2000)
        assert ratio < 8, f"4x the openers took {ratio:.1f}x the time"

    def test_nested_quotes_scale_linearly(self):
        def best_of_three(text):
            best = float("inf")
            for _ in range(3):
                start = time.perf_counter()
                marko.convert(text)
                best = min(best, time.perf_counter() - start)
            return best

        ratio = best_of_three("> " * 24 + "a") / best_of_three("> " * 12 + "a")
        assert ratio < 8, f"2x the depth took {ratio:.1f}x the time"

    @pytest.mark.parametrize("opener", ["[", "!["])
    @pytest.mark.parametrize("definition", ["", "\n\n[a]: /url\n"])
    def test_bracket_runs_scale_linearly(self, opener, definition):
        def best_of_three(n):
            best = float("inf")
            for _ in range(3):
                start = time.perf_counter()
                marko.convert(opener * n + "]" * n + definition)
                best = min(best, time.perf_counter() - start)
            return best

        ratio = best_of_three(8000) / best_of_three(2000)
        assert ratio < 8, f"4x the brackets took {ratio:.1f}x the time"

    def test_link_destination_paren_nesting_limit(self):
        nested = "(" * 32 + ")" * 32
        assert f'href="{nested}"' in marko.convert(f"[a]({nested})")
        too_deep = "(" * 33 + ")" * 33
        assert "<a" not in marko.convert(f"[a]({too_deep})")

    def test_quote_marker_takes_the_following_space(self):
        # The space after ">" belongs to the marker, so "  > b" is not indented
        # enough to continue the list item and starts a quote after the list.
        assert marko.convert("> - a\n>\n>  > b\n") == (
            "<blockquote>\n<ul>\n<li>a</li>\n</ul>\n"
            "<blockquote>\n<p>b</p>\n</blockquote>\n</blockquote>\n"
        )

    def test_nested_containers_with_lazy_continuation(self):
        text = "> - a\n>   - b\nlazy\n> - c\n>\n>   para\n"
        assert marko.convert(text) == (
            "<blockquote>\n<ul>\n<li>\n<p>a</p>\n<ul>\n<li>b\nlazy</li>\n</ul>\n"
            "</li>\n<li>\n<p>c</p>\n<p>para</p>\n</li>\n</ul>\n</blockquote>\n"
        )

    def test_link_ref_defs_in_list_items_still_resolve(self):
        text = "".join(f"- [l{i}]: /u{i}\n" for i in range(50)) + "\n[l0] [l49]\n"
        html = marko.convert(text)
        assert '<a href="/u0">l0</a>' in html
        assert '<a href="/u49">l49</a>' in html

    def test_cr_line_terminator_no_infinite_loop(self):
        assert marko.convert("-\r-") == marko.convert("-\n-")

    @pytest.mark.parametrize(
        "text",
        ["-\f-", "a\f# b", "a\f- b", "a\f> b", "1.\fx", "a\f```\nb"],
    )
    def test_form_feed_is_not_a_line_ending(self, text):
        # A form feed is whitespace inside a line, not a line ending, so it must
        # not start a new block. It used to send list parsing into a loop.
        assert marko.convert(text) == f"<p>{html.escape(text, quote=False)}</p>\n"

    @pytest.mark.parametrize(
        "text, paragraph",
        [
            ('[foo]: /url\n"title\n\n[foo]', "<p>&quot;title</p>"),
            ("[foo]: /url\n'title\n\n[foo]", "<p>'title</p>"),
            ("[foo]: /url\n(title\n\n[foo]", "<p>(title</p>"),
            ('[foo]: /url\n"title\n\nmore"\n\n[foo]', "<p>&quot;title</p>"),
        ],
    )
    def test_link_ref_def_with_invalid_title_on_next_line(self, text, paragraph):
        res = marko.convert(text)
        assert res.startswith(paragraph + "\n")
        assert '<p><a href="/url">foo</a></p>' in res

    def test_cdata_html_block_ends_at_cdata_end(self):
        res = marko.convert("<![CDATA[\na > b\nc\n]]>\nfoo\n")
        assert res == "<![CDATA[\na > b\nc\n]]>\n<p>foo</p>\n"

    @pytest.mark.parametrize("text", ["<! x\n", "<!1\n", "<![x\n"])
    def test_declaration_html_block_needs_a_letter(self, text):
        assert marko.convert(text).startswith("<p>&lt;!")

    @pytest.mark.parametrize(
        "text, html",
        [
            ("[foo]: /url(\n\n[foo]", "<p>[foo]: /url(</p>\n<p>[foo]</p>\n"),
            ("[foo]: /url(bar\n\n[foo]", "<p>[foo]: /url(bar</p>\n<p>[foo]</p>\n"),
            ('[foo](/url( "title")', "<p>[foo](/url( &quot;title&quot;)</p>\n"),
        ],
    )
    def test_link_dest_with_unbalanced_parenthesis(self, text, html):
        assert marko.convert(text) == html

    def test_long_paragraph_with_many_links_and_emphasis(self):
        text = " ".join(f"*e{i}* [l{i}](/u{i}) `c` \\* x" for i in range(200))
        html = marko.convert(text)
        assert html.count("<a href=") == 200
        assert html.count("<em>") == 200
        assert html.count("<code>c</code>") == 200
        assert html.count(" * x") == 200
        assert '<a href="/u199">l199</a>' in html

    @pytest.mark.parametrize(
        "html", ["<!doctype html>", "<!X>", "<!ELEMENT br EMPTY>", "<!x\ny>"]
    )
    def test_inline_declaration(self, html):
        assert marko.convert(f"a {html} b") == f"<p>a {html} b</p>\n"

    def test_xml_renderer(self):
        text = "[Overview](#overview)\n\n* * *"
        markdown = marko.Markdown(renderer=XMLRenderer)
        res = markdown(text)
        assert '<?xml version="1.0" encoding="UTF-8"?>' in res
        assert 'dest="#overview"' in res

    def test_ast_renderer(self):
        text = "[Overview](#overview)\n\n* * *"
        markdown = marko.Markdown(renderer=ASTRenderer)
        res = markdown(text)
        assert isinstance(res, dict)
        assert res["element"] == "document"
        assert res["children"][0]["element"] == "paragraph"

    def test_ast_renderer_unescape_raw_text(self):
        markdown = marko.Markdown(renderer=ASTRenderer)
        res = markdown("&lt;&#42;")
        assert res["children"][0]["children"][0]["children"] == "<*"

        res = markdown("    &lt;&#42;")
        assert res["children"][0]["children"][0]["children"] == "&lt;&#42;\n"

    def test_markdown_renderer(self):
        with open("tests/samples/syntax.md", encoding="utf-8") as f:
            text = f.read()

        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert normalize_html(marko.convert(rerendered)) == normalize_html(
            marko.convert(text)
        )

    def test_markdown_renderer_loose_list(self):
        # A loose list (items separated by blank lines) must round-trip unchanged.
        # Before the fix, render_list() emitted tight spacing regardless of
        # element.tight, converting the loose list to a tight list and producing
        # different HTML output.
        for text in (
            "- item1\n\n- item2\n",
            "- a\n\n- b\n\n- c\n",
            "1. first\n\n2. second\n",
        ):
            markdown = marko.Markdown(renderer=MarkdownRenderer)
            rerendered = markdown(text)
            assert (
                rerendered == text
            ), f"loose list not preserved: {text!r} -> {rerendered!r}"
            assert normalize_html(marko.convert(rerendered)) == normalize_html(
                marko.convert(text)
            )

    @pytest.mark.parametrize(
        "text",
        [
            "> foo\n>\n> bar\n",
            "> # Title\n>\n> text\n",
            "> - a\n>\n> - b\n",
            "> > foo\n> >\n> > bar\n",
            "- a\n\n  > q1\n  >\n  > q2\n",
        ],
    )
    def test_markdown_renderer_quote_with_blank_lines(self, text):
        # A blank line inside a block quote keeps its ">", so the quote isn't split.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == text
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize(
        "text",
        [
            "> <details>\n> <summary>More</summary>\n> Hidden text\n> </details>\n",
            "> <!--\n> a comment\n>\n> more\n> -->\n",
            "- <div>\n  <p>inside</p>\n  </div>\n",
            "1. <table>\n   <tr><td>x</td></tr>\n   </table>\n",
            "<div>\nplain\n</div>\n",
        ],
    )
    def test_markdown_renderer_html_block_in_container(self, text):
        # Every line of an HTML block keeps the quote markers or list indentation.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == text
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize(
        "text",
        [
            "Foo\nBar\n---\n",
            "Foo *bar\nbaz*\n===\n",
            "> Foo\n> Bar\n> ===\n",
            "- Foo\n  Bar\n  ---\n",
        ],
    )
    def test_markdown_renderer_multiline_setext_heading(self, text):
        # A heading on several lines stays a setext heading; an ATX one would
        # keep only the first line.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == text
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize(
        "text",
        [
            "1) one\n2) two\n",
            "1. foo\n2. bar\n3) baz\n",
            "3) start at three\n",
            "> 1) quoted\n",
        ],
    )
    def test_markdown_renderer_ordered_list_delimiter(self, text):
        # "1." and "1)" are different list markers; a change of marker starts a new list.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == text
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize(
        "text",
        [
            "- foo\n-\n- bar\n",
            "1. foo\n2.\n3. bar\n",
            "*\n",
            "> - a\n> -\n",
            "- a\n\n-\n\n- b\n",
        ],
    )
    def test_markdown_renderer_empty_list_item(self, text):
        # An empty list item keeps its marker.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == text
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize(
        "text",
        [
            "   - foo\n\n    code\n",
            "  2. foo\n\n\tcode\n",
            "  1. foo\n  2. bar\n\n    code\n",
            "- foo\n\n     - bar\n\n      code\n",
            ">   1) foo\n>\n>     code\n",
        ],
    )
    def test_markdown_renderer_list_before_indented_code(self, text):
        # The code block stays after the list instead of joining its last item.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert marko.convert(rerendered) == marko.convert(text)
        assert "<pre><code>" in marko.convert(rerendered)

    @pytest.mark.parametrize(
        "text",
        [
            "Contact <foo@bar.example.com>.\n",
            "<foo+special@Bar.baz-bar0.com>\n",
            "<mailto:foo@bar.example.com>\n",
            "<https://example.com/a_b>\n",
        ],
    )
    def test_markdown_renderer_auto_link(self, text):
        # An email address is not written with the "mailto:" of its destination.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == text
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("**_foo_**\n", "**_foo_**\n"),
            ("__*foo*__\n", "**_foo_**\n"),
            ("*_foo_*\n", "*_foo_*\n"),
            ("**_*foo*_**\n", "**_*foo*_**\n"),
            ("- **_Note:_** bar\n", "- **_Note:_** bar\n"),
            ("***foo***\n", "***foo***\n"),
            ("foo***bar***baz\n", "foo***bar***baz\n"),
        ],
    )
    def test_markdown_renderer_nested_emphasis(self, text, expected):
        # Emphasis directly in emphasis keeps its delimiters apart from the outer ones.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == expected
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Foo\n    ***\n", "Foo\n\\***\n"),
            ("foo\n    # bar\n", "foo\n\\# bar\n"),
            ("Foo\n    ---\n", "Foo\n\\---\n"),
            ("Foo\n    =\n", "Foo\n\\=\n"),
            ("foo\n    - bar\n", "foo\n\\- bar\n"),
            ("foo\n    1. bar\n", "foo\n1\\. bar\n"),
            ("foo\n    > bar\n", "foo\n\\> bar\n"),
            ("foo\n    ```\n", "foo\n\\```\n"),
            ("> foo\n    - bar\n", "> foo\n\\- bar\n"),
            ("- a\n - b\n  - c\n   - d\n    - e\n", "- a\n- b\n- c\n- d\n\\- e\n"),
            # lines that cannot start a block are left alone
            ("foo\n    2. bar\n    -bar\n    #5\n", "foo\n2. bar\n-bar\n#5\n"),
        ],
    )
    def test_markdown_renderer_paragraph_continuation_block_start(self, text, expected):
        # A continuation line loses its indentation, so a leading block marker
        # is escaped to keep it in the paragraph.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == expected
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize(
        "text",
        [
            "- foo [x]\n\n  [x]: /url\n",
            '- foo [x]\n\n  [x]: /url "Title"\n\n- bar\n',
            "> [foo]: /url\n\n[foo]\n",
            "> foo\n>\n> [r]: /url\n> bar [r]\n",
        ],
    )
    def test_markdown_renderer_link_ref_def_in_container(self, text):
        # A link reference definition in a list item or a quote stays in it.
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == text
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize(
        "text",
        [
            "```\n```\n",
            "```\n\n```\n",
            "```\ncode\n\n```\n",
            "```python\ncode\n```\n",
            "````python\nbefore\n```\nafter\n````\n",
            "~~~\nbefore\n```\nafter\n~~~\n",
            "~~~\n``````\n```\n~~~\n",
            "~~~\n  ```\t\n~~~\n",
            "~~~c`lang\ncode\n~~~\n",
            "~~~python extra`info\ncode\n~~~\n",
            "~~~ ~`lang\ncode\n~~~\n",
            "> ~~~\n> ```\n> ~~~\n",
            "- ~~~\n  ```\n  ~~~\n",
        ],
    )
    def test_markdown_renderer_code_fence_roundtrip(self, text):
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert marko.convert(rerendered) == marko.convert(text)

    @pytest.mark.parametrize("separator", ["\v", "\x85", "\u2028", "\u2029"])
    @pytest.mark.parametrize(
        "template",
        [
            "```\na{}b\n```\n",
            "    a{}b\n",
            "> ```\n> a{}b\n> ```\n",
            ">     a{}b\n",
            "- ```\n  a{}b\n  ```\n",
            "- item\n\n      a{}b\n",
        ],
    )
    def test_markdown_renderer_preserves_code_block_separators(
        self, separator, template
    ):
        text = template.format(separator)
        markdown = marko.Markdown(renderer=MarkdownRenderer)

        rerendered = markdown(text)

        assert separator in rerendered
        assert marko.convert(rerendered) == marko.convert(text)
        assert markdown(rerendered) == rerendered

    @pytest.mark.parametrize(
        "text",
        [
            "`code`",
            "``a`b``",
            "``` ``x`` ```",
            "````a`b``c```d````",
            "`` ` ``",
            "```` ``` ````",
            "`` `a` ``",
            "`  a  `",
            "` a`",
            "`a `",
            "`   `",
        ],
    )
    def test_markdown_renderer_code_span_roundtrip(self, text):
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert rerendered == text + "\n"
        assert marko.convert(rerendered) == marko.convert(text)

    def test_markdown_renderer_preserve_link_refs(self):
        text = textwrap.dedent("""\
            This is a [link ref][1], [1] and a [link](abc "title").
            This is a footnote [^1].

            [1]: def
            [^1]: ghi
            """)
        markdown = marko.Markdown(renderer=MarkdownRenderer, extensions=["footnote"])
        rerendered = markdown.convert(text)
        assert rerendered == text

    @pytest.mark.parametrize("image", [False, True])
    @pytest.mark.parametrize("title", ["", ' "A title"'])
    @pytest.mark.parametrize(
        "destination",
        [
            "plain.pdf",
            "<my file.pdf>",
            "<my\tfile.pdf>",
            r"foo\)bar",
            r"foo\(bar",
            "foo(bar)",
            r"foo\\*bar",
            r"foo\\bar",
            r"foo\<bar\>",
            r"<my file\>name.pdf>",
            "<>",
            "file&amp;name.pdf",
        ],
    )
    def test_markdown_renderer_link_destinations(self, image, title, destination):
        text = f"{'!' if image else ''}[doc]({destination}{title})"
        markdown = marko.Markdown(renderer=MarkdownRenderer)
        expected = marko.convert(text)
        assert ("<img " if image else "<a ") in expected

        rerendered = markdown(text)
        assert marko.convert(rerendered) == expected
        assert markdown(rerendered) == rerendered


class TestExtension:
    def test_extension_use(self):
        markdown = marko.Markdown(extensions=["footnote", "toc"])

        assert len(markdown._extra_elements) == 3
        assert len(markdown._renderer_mixins) == 2
        assert hasattr(markdown._renderer_mixins[1], "render_footnote_def")

    def test_extension_setup(self):
        markdown = marko.Markdown()
        markdown.use("footnote")

        markdown.convert("abc")
        with pytest.raises(marko.SetupDone, match="Unable to register more extensions"):
            markdown.use("toc")

        assert hasattr(markdown.renderer, "render_footnote_def")

    def test_extension_override(self):
        class MyRendererMixin:
            def render_paragraph(self, element):
                return "foo bar"

        my_extension = marko.MarkoExtension(renderer_mixins=[MyRendererMixin])

        markdown = marko.Markdown(extensions=["gfm", my_extension])
        out = markdown.convert("hello world\n")
        assert out == "foo bar"

    def test_extension_override_element(self):
        class MyHeading(block.Heading):
            override = True

        my_extension = marko.MarkoExtension(elements=[MyHeading])

        markdown = marko.Markdown(extensions=[my_extension])
        markdown._setup_extensions()
        assert markdown.parser.block_elements["Heading"] is MyHeading
        assert markdown.parser.block_elements["Heading"].get_type() == "Heading"

    def test_extension_override_non_base_element(self):
        class MyHeading(block.BlockElement):
            override = True

        my_extension = marko.MarkoExtension(elements=[MyHeading])

        markdown = marko.Markdown(extensions=[my_extension])
        markdown._setup_extensions()
        assert markdown.parser.block_elements["MyHeading"] is MyHeading
        assert markdown.parser.block_elements["MyHeading"].get_type() == "MyHeading"

    def test_extension_with_illegal_element(self):
        my_extension = marko.MarkoExtension(elements=[object])  # type: ignore

        markdown = marko.Markdown(extensions=[my_extension])
        with pytest.raises(TypeError, match="The element should be a subclass of"):
            markdown.convert("hello world\n")

    def test_no_delegate_render_methods(self):
        class RendererMixin:
            def render_paragraph(self, element):
                return "ohohohohohoh"

        my_extension = marko.MarkoExtension(renderer_mixins=[RendererMixin])

        markdown = marko.Markdown(renderer=ASTRenderer, extensions=[my_extension])
        res = markdown.convert("Hello world")
        paragraph = res["children"][0]
        assert isinstance(paragraph, dict)
        assert paragraph["element"] == "paragraph"

        raw_text = paragraph["children"][0]
        assert raw_text["children"] == "Hello world"

    def test_gfm_markdown_renderer(self):
        text = textwrap.dedent("""\
            ## TODO

            - [x] Shopping[^1]
            - [ ] ~~Study~~

            ## Table

            | Item | Price |
            | ---- | ----- |
            | Apple | $1 |
            | Orange | $2 |

            > [!CAUTION]
            > Upcoming bugs

            [^1]: go to https://example.com
            """)

        md = marko.Markdown(extensions=["gfm", "footnote"], renderer=MarkdownRenderer)
        res = md.convert(text)
        assert res == text

    def test_paragraph_breaking_element(self):
        class CustomElement(block.BlockElement):
            breaks_paragraph = True
            pattern = re.compile(r" {,3}@broken (.*)", flags=re.MULTILINE)

            def __init__(self, match: re.Match[str]) -> None:
                self.inline_body = match.group(1).strip()

            @classmethod
            def match(cls, source: Source) -> re.Match[str] | None:
                return source.expect_re(cls.pattern)

            @classmethod
            def parse(cls, source: Source) -> re.Match[str] | None:
                m = source.match
                source.consume()
                return m

        my_extension = marko.MarkoExtension(elements=[CustomElement])

        text = textwrap.dedent("""
            some text that is
            @broken by a custom element
            """)

        md = marko.Markdown(extensions=[my_extension])
        res = md.parse(text)

        assert len(res.children) == 4
        assert isinstance(res.children[0], block.BlankLine)
        assert isinstance(res.children[1], block.Paragraph)
        assert isinstance(res.children[2], CustomElement)
        assert isinstance(res.children[3], block.BlankLine)
