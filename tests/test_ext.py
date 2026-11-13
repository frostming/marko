import pytest

from marko import Markdown


class TestFootnote:
    def setup_method(self):
        self.markdown = Markdown()
        self.markdown.use("footnote")

    def test_footnote(self):
        result = self.markdown("this is a footnote[^1].\n\n[^1]: foo\n")
        assert '<sup class="footnote-ref"' in result
        assert 'foo<a href="#fnref-1" class="footnote">&#8617;</a>' in result

    @pytest.mark.parametrize("body", ["Detail.", "- Detail."])
    @pytest.mark.parametrize(
        "label, escaped",
        [
            ("chapter one", "chapter%20one"),
            (r"section\g", "section%5Cg"),
            ('double"quote', "double%22quote"),
        ],
    )
    def test_footnote_backlink_escapes_label(self, body, label, escaped):
        result = self.markdown(f"Example[^{label}]\n\n[^{label}]: {body}\n")
        assert f'id="fnref-{escaped}"' in result
        assert f'<a href="#fnref-{escaped}" class="footnote">' in result

    def test_non_footnote(self):
        result = self.markdown("foo[^1]")
        assert result.rstrip() == "<p>foo[^1]</p>"


class TestToc:
    def setup_method(self):
        self.markdown = Markdown()
        self.markdown.use("toc")

    def test_render_toc(self):
        content = "# Foo\n## Foobar\n## Foofooz\n# Bar\n"
        result = self.markdown(content)
        assert '<h1 id="foo">Foo</h1>' in result
        toc = self.markdown.renderer.render_toc()
        assert '<ul>\n<li><a href="#foo">Foo</a></li>' in toc
        assert '<ul>\n<li><a href="#foobar">Foobar</a></li>' in toc

    def test_render_toc_exceeding_maxdepth(self):
        content = "#### Foobar\n"
        self.markdown(content)
        toc = self.markdown.renderer.render_toc()
        assert '<li><a href="#foobar">Foobar</a></li>' in toc
        content = "# Foo\n#### Foobar\n"
        self.markdown(content)
        toc = self.markdown.renderer.render_toc()
        assert '<li><a href="#foo">Foo</a></li>' in toc
        assert '<li><a href="#foobar">Foobar</a></li>' not in toc

    def test_render_toc_replace_tags(self):
        from marko.ext.toc import make_extension as Toc

        markdown = Markdown(extensions=[Toc("<div>", "</div>")])
        content = "#### Foobar\n"
        markdown(content)
        toc = markdown.renderer.render_toc()
        assert "<div>\n" in toc
        assert "</div>\n" in toc


class TestPangu:
    def setup_method(self):
        self.markdown = Markdown()
        self.markdown.use("pangu")

    def test_render_pangu(self):
        content = "中国2018年"
        result = self.markdown(content)
        assert (
            result
            == '<p>中国<span class="pangu"></span>2018<span class="pangu"></span>年</p>\n'
        )

    def test_chinese_punctuations(self):
        content = "你好：中国。"
        result = self.markdown(content)
        assert result == "<p>你好：中国。</p>\n"


class TestCodeHilite:
    def setup_method(self):
        self.markdown = Markdown(extensions=["codehilite"])

    def test_render_fenced_code(self):
        content = '```python\nprint("hello")\n```'
        assert '<div class="highlight">' in self.markdown(content)
        content = '```foobar\nprint("hello")\n```'
        # Fallback to normal output.
        assert '<div class="highlight">' in self.markdown(content)

    def test_render_code_block(self):
        content = '    print("hello")\n'
        assert '<div class="highlight">' in self.markdown(content)

    def test_codehilite_options(self):
        from marko.ext.codehilite import make_extension

        markdown = Markdown(extensions=[make_extension(linenos="table")])
        content = '```python\nprint("hello")\n```'
        assert '<table class="highlighttable">' in markdown(content)

    def test_render_code_block_with_extra(self):
        content = '```python filename="test.py"\nprint("hello")\n```'
        assert '<span class="filename">test.py</span>' in self.markdown(content)


class TestGFMAlert:
    def setup_method(self):
        from marko import Markdown
        from marko.ast_renderer import ASTRenderer
        from marko.ext.gfm import GFM

        self.md_ast = Markdown(renderer=ASTRenderer, extensions=[GFM])
        self.md_html = Markdown(extensions=[GFM])

    @pytest.mark.parametrize(
        "alert_type", ["WARNING", "CAUTION", "TIP", "warning", "Caution"]
    )
    def test_alert_ast(self, alert_type):
        text = f"> [!{alert_type}]\n> Foo bar\n> Bar\n"
        ast = self.md_ast(text)
        admon = ast["children"][0]
        assert admon["element"] == "alert"
        assert admon["alert_type"] == alert_type.upper()
        inner = admon["children"][0]["children"]
        assert inner[0]["children"] == "Foo bar"
        assert inner[1]["element"] == "line_break"
        assert inner[2]["children"] == "Bar"

    @pytest.mark.parametrize(
        "alert_type", ["WARNING", "CAUTION", "TIP", "warning", "Caution"]
    )
    def test_alert_html(self, alert_type):
        text = f"> [!{alert_type}]\n> Foo bar\n> Bar\n"
        html = self.md_html(text)
        assert f'<blockquote class="alert alert-{alert_type.lower()}">' in html
        assert f"<p>{alert_type.title()}</p>" in html
        assert "<p>Foo bar\nBar</p>" in html

    def test_alert_disallow_content_on_header_line(self):
        text = "> [!NOTE] This is not allowed.\n> Foo bar\n"
        html = self.md_html(text)
        # Should be treated as a normal blockquote.
        assert "<blockquote>\n<p>[!NOTE] This is not allowed." in html


class TestGFMTableLlistElement:
    def setup_method(self):
        from marko import Markdown
        from marko.ext.gfm import GFM
        from marko.md_renderer import MarkdownRenderer

        self.md_md = Markdown(renderer=MarkdownRenderer, extensions=[GFM])

    def test_render_table_in_list_indented(self):
        text = "- Item.\n\n  |foo|bar|\n  |---|---|\n  |foo|bar|"
        md = self.md_md(text)
        assert md == "- Item.\n\n  | foo | bar |\n  | --- | --- |\n  | foo | bar |\n"

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("foo\n    # bar\n", "foo\n\\# bar\n"),
            ("> foo\n    - bar\n", "> foo\n\\- bar\n"),
            ("- [ ] foo\n      ***\n", "- [ ] foo\n\\***\n"),
        ],
    )
    def test_render_paragraph_continuation_block_start(self, text, expected):
        # The GFM paragraph escapes a block marker on a continuation line too.
        md = self.md_md(text)
        assert md == expected
        html = Markdown(extensions=["gfm"])
        assert html(md) == html(text)

    @pytest.mark.parametrize(
        "text",
        [
            "www.commonmark.org\n",
            "Visit www.commonmark.org/help for more information.\n",
            "Visit www.commonmark.org.\n",
            "www.google.com/search?q=Markup+(business)))\n",
            "(www.google.com/search?q=Markup+(business))\n",
            "www.google.com/search?q=commonmark&hl;\n",
            "www.commonmark.org/he<lp\n",
            "foo@bar.baz\n",
            "a.b-c_d@a.b\n\na.b-c_d@a.b.\n\na.b-c_d@a.b-\n\na.b-c_d@a.b_\n",
            "hello@mail+xyz.example isn't valid, but hello+xyz@mail.example is.\n",
            "http://commonmark.org\n",
            "**www.commonmark.org is great**\n",
        ],
    )
    def test_render_url_keeps_original_text(self, text):
        # A GFM bare autolink must re-render as the matched text, not as the
        # normalized destination, or the link text changes (and email
        # addresses get mangled) on the next parse. See #325.
        rerendered = self.md_md(text)
        assert rerendered == text
        html = Markdown(extensions=["gfm"])
        assert html(rerendered) == html(text)
        assert self.md_md(rerendered) == rerendered
