from marko import Markdown


class TestFootnote:
    def setup_method(self):
        self.markdown = Markdown()
        self.markdown.use("footnote")

    def test_footnote(self):
        result = self.markdown("this is a footnote[^1].\n\n[^1]: foo\n")
        assert '<sup class="footnote-ref"' in result
        assert 'foo<a href="#fnref-1" class="footnote">&#8617;</a>' in result

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

    def test_alert_ast(self):
        text = "> [!WARNING]\n> Foo bar\n> Bar\n"
        ast = self.md_ast(text)
        admon = ast["children"][0]
        assert admon["element"] == "alert"
        assert admon["alert_type"] == "WARNING"
        inner = admon["children"][0]["children"]
        assert inner[0]["children"] == "Foo bar"
        assert inner[1]["element"] == "line_break"
        assert inner[2]["children"] == "Bar"

    def test_alert_html(self):
        text = "> [!WARNING]\n> Foo bar\n> Bar\n"
        html = self.md_html(text)
        assert '<blockquote class="alert alert-warning">' in html
        assert "<p>Warning</p>" in html
        assert "<p>Foo bar\nBar</p>" in html
