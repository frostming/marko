#! -*- coding: utf-8 -*-
from __future__ import unicode_literals

from marko import Markdown


class TestFootnote:

    def setup_method(self):
        self.markdown = Markdown()
        self.markdown.use('footnote')

    def test_footnote(self):
        result = self.markdown('this is a footnote[^1].\n\n[^1]: foo\n')
        assert '<sup class="footnote-ref"' in result
        assert 'foo<a href="#fnref-1" class="footnote">&#8617;</a>' in result

    def test_non_footnote(self):
        result = self.markdown('foo[^1]')
        assert result.rstrip() == '<p>foo[^1]</p>'


class TestToc:

    def setup_method(self):
        self.markdown = Markdown()
        self.markdown.use('toc')

    def test_render_toc(self):
        content = '# Foo\n## Foobar\n## Foofooz\n# Bar\n'
        result = self.markdown(content)
        assert '<h1 id="foo">Foo</h1>' in result
        toc = self.markdown.renderer.render_toc()
        assert '<ul>\n<li><a href="#foo">Foo</a></li>' in toc
        assert '<ul>\n<li><a href="#foobar">Foobar</a></li>' in toc

    def test_render_toc_exceeding_maxdepth(self):
        content = '#### Foobar\n'
        self.markdown(content)
        toc = self.markdown.renderer.render_toc()
        assert '<li><a href="#foobar">Foobar</a></li>' in toc
        content = '# Foo\n#### Foobar\n'
        self.markdown(content)
        toc = self.markdown.renderer.render_toc()
        assert '<li><a href="#foo">Foo</a></li>' in toc
        assert '<li><a href="#foobar">Foobar</a></li>' not in toc


class TestPangu:

    def setup_method(self):
        self.markdown = Markdown()
        self.markdown.use('pangu')

    def test_render_pangu(self):
        content = '中国2018年'
        result = self.markdown(content)
        assert (
            result ==
            '<p>中国<span class="pangu"></span>2018<span class="pangu"></span>年</p>\n'
        )

    def test_chinese_punctuations(self):
        content = '你好：中国。'
        result = self.markdown(content)
        assert result == '<p>你好：中国。</p>\n'


class TestGFM:

    def setup_method(self):
        from marko.ext.gfm import gfm

        self.markdown = gfm

    def test_gfm_autolink(self):
        content = '地址：https://google.com'
        assert self.markdown(content).strip() == '<p>地址：<a href="https://google.com">https://google.com</a></p>'
        content = '地址：www.baidu.com'
        assert self.markdown(content).strip() == '<p>地址：<a href="http://www.baidu.com">www.baidu.com</a></p>'


class TestCodeHilite:

    def setup_method(self):
        self.markdown = Markdown(extensions=['codehilite'])

    def test_render_fenced_code(self):
        content = '```python\nprint("hello")\n```'
        assert '<div class="highlight">' in self.markdown(content)
        content = '```foobar\nprint("hello")\n```'
        # Fallback to normal output.
        result = self.markdown(content)
        assert '<div class="highlight">' not in result
        assert '<pre><code class="language-foobar">' in result

    def test_render_code_block(self):
        content = '    print("hello")\n'
        assert '<pre><code>' in self.markdown(content)
