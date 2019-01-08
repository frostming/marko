#! -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
        from marko import HTMLRenderer, Markdown
        from marko.ext.toc import TocRendererMixin

        class MyRenderer(TocRendererMixin, HTMLRenderer):
            pass

        self.markdown = Markdown(renderer=MyRenderer)

    def test_render_toc(self):
        content = '# Foo\n## Foobar\n## Foofooz\n# Bar\n'
        result = self.markdown(content)
        self.assertIn('<h1 id="foo">Foo</h1>', result)
        toc = self.markdown.renderer.render_toc()
        self.assertIn('<ul>\n<li><a href="#foo">Foo</a></li>', toc)
        self.assertIn('<ul>\n<li><a href="#foobar">Foobar</a></li>', toc)

    def test_render_toc_exceeding_maxdepth(self):
        content = '#### Foobar\n'
        self.markdown(content)
        toc = self.markdown.renderer.render_toc()
        self.assertIn('<li><a href="#foobar">Foobar</a></li>', toc)
        content = '# Foo\n#### Foobar\n'
        self.markdown(content)
        toc = self.markdown.renderer.render_toc()
        self.assertIn('<li><a href="#foo">Foo</a></li>', toc)
        self.assertNotIn('<li><a href="#foobar">Foobar</a></li>', toc)


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

    def test_chinese_punctuations(self):
        content = '你好：中国。'
        result = self.markdown(content)
        self.assertEqual(result, '<p>你好：中国。</p>\n')


class TestGFM(unittest.TestCase):

    def setUp(self):
        from marko.ext.gfm import GFMarkdown

        self.markdown = GFMarkdown()

    def test_gfm_autolink(self):
        content = '地址：https://google.com'
        self.assertEqual(self.markdown(content).strip(), '<p>地址：<a href="https://google.com">https://google.com</a></p>')
        content = '地址：www.baidu.com'
        self.assertEqual(self.markdown(content).strip(), '<p>地址：<a href="http://www.baidu.com">www.baidu.com</a></p>')


if __name__ == '__main__':
    unittest.main()
