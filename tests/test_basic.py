#! -*- coding: utf-8 -*-
import pytest
import marko
from tests.normalize import normalize_html


class TestBasic:

    def test_xml_renderer(self):
        from marko.ast_renderer import XMLRenderer

        text = "[Overview](#overview)"
        markdown = marko.Markdown(renderer=XMLRenderer)
        res = markdown(text)
        assert '<?xml version="1.0" encoding="UTF-8"?>' in res
        assert 'dest="#overview"' in res

    def test_ast_renderer(self):
        from marko.ast_renderer import ASTRenderer

        text = "[Overview](#overview)"
        markdown = marko.Markdown(renderer=ASTRenderer)
        res = markdown(text)
        assert isinstance(res, dict)
        assert res['element'] == 'document'
        assert res['children'][0]['element'] == 'paragraph'

    def test_markdown_renderer(self):
        from marko.md_renderer import MarkdownRenderer

        with open('tests/samples/syntax.md') as f:
            text = f.read()

        markdown = marko.Markdown(renderer=MarkdownRenderer)
        rerendered = markdown(text)
        assert (
            normalize_html(marko.convert(rerendered))
            == normalize_html(marko.convert(text))
        )


class TestExtension:

    def test_extension_use(self):

        markdown = marko.Markdown(extensions=['footnote', 'toc'])

        assert len(markdown._extra_elements) == 3
        assert len(markdown._renderer_mixins) == 2
        assert hasattr(markdown._renderer_mixins[1], 'render_footnote_def')

    def test_extension_setup(self):

        markdown = marko.Markdown()
        markdown.use('footnote')

        markdown.convert('abc')
        with pytest.raises(marko.SetupDone):
            markdown.use('toc')

        assert hasattr(markdown.renderer, 'render_footnote_def')

    def test_extension_override(self):

        class MyRendererMixin:
            def render_paragraph(self, element):
                return 'foo bar'

        class MyExtension:
            renderer_mixins = [MyRendererMixin]

        markdown = marko.Markdown(extensions=['gfm', MyExtension])
        out = markdown.convert('hello world\n')
        assert out == 'foo bar'

    def test_extension_deprecation(self):
        from marko.ext.footnote import FootnoteExtension

        markdown = marko.Markdown()
        with pytest.warns(DeprecationWarning):
            markdown.use(FootnoteExtension)
