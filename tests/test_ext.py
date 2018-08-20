import unittest


class TestFootnote(unittest.TestCase):

    def setUp(self):
        from marko import Parser, HTMLRenderer, Markdown
        from marko.ext.footnote import FootnoteParserMixin, FootnoteRendererMixin

        class MyParser(FootnoteParserMixin, Parser):
            pass

        class MyRenderer(FootnoteRendererMixin, HTMLRenderer):
            pass

        self.markdown = Markdown(MyParser, MyRenderer)

    def test_footnote(self):
        result = self.markdown('this is a footnote[^1].\n\n[^1]: foo\n')
        self.assertIn('<sup class="footnote-ref"', result)
        self.assertIn('foo<a href="#fnref-1" class="footnote">&#8617;</a>', result)

    def test_non_footnote(self):
        result = self.markdown('foo[^1]')
        self.assertEqual(result.rstrip(), '<p>foo[^1]</p>')


class TestToc(unittest.TestCase):

    def setUp(self):
        from marko import Parser, HTMLRenderer, Markdown
        from marko.ext.toc import TocParserMixin, TocRendererMixin

        class MyParser(TocParserMixin, Parser):
            pass

        class MyRenderer(TocRendererMixin, HTMLRenderer):
            pass

        self.markdown = Markdown(MyParser, MyRenderer)

    def test_render_toc(self):
        content = '# Foo\n## Foobar\n## Foofooz\n# Bar\n'
        result = self.markdown(content)
        self.assertIn('<h1 id="foo">Foo</h1>', result)
        toc = self.markdown.renderer.render_toc()
        self.assertIn('<ul>\n<li><a href="#foo">Foo</a></li>', toc)
        self.assertIn('<ul>\n<li><a href="#foobar">Foobar</a></li>', toc)


class TestPangu(unittest.TestCase):

    def setUp(self):
        from marko import Markdown, HTMLRenderer
        from marko.ext.pangu import PanguRendererMixin

        class MyRenderer(PanguRendererMixin, HTMLRenderer):
            pass

        self.markdown = Markdown(renderer=MyRenderer)

    def test_render_pangu(self):
        content = '中国2018年'
        result = self.markdown(content)
        self.assertEqual(
            result,
            '<p>中国<span class="pangu"></span>2018<span class="pangu"></span>年</p>\n'
        )


if __name__ == '__main__':
    unittest.main()
