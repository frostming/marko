#! -*- coding: utf-8 -*-
import pytest

import marko
from marko import block
from marko.ast_renderer import ASTRenderer, XMLRenderer
from marko.md_renderer import MarkdownRenderer

from tests.normalize import normalize_html


class TestBasic:
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

        class MyExtension:
            renderer_mixins = [MyRendererMixin]

        markdown = marko.Markdown(extensions=["gfm", MyExtension])
        out = markdown.convert("hello world\n")
        assert out == "foo bar"

    def test_extension_override_element(self):
        class MyHeading(block.Heading):
            override = True

        class MyExtension:
            elements = [MyHeading]

        markdown = marko.Markdown(extensions=[MyExtension])
        markdown._setup_extensions()
        assert markdown.parser.block_elements["Heading"] is MyHeading
        assert markdown.parser.block_elements["Heading"].get_type() == "Heading"

    def test_extension_override_non_base_element(self):
        class MyHeading(block.BlockElement):
            override = True

        class MyExtension:
            elements = [MyHeading]

        markdown = marko.Markdown(extensions=[MyExtension])
        markdown._setup_extensions()
        assert markdown.parser.block_elements["MyHeading"] is MyHeading
        assert markdown.parser.block_elements["MyHeading"].get_type() == "MyHeading"

    def test_extension_with_illegal_element(self):
        class MyExtension:
            elements = [object]

        markdown = marko.Markdown(extensions=[MyExtension])
        with pytest.raises(TypeError, match="The element should be a subclass of"):
            markdown.convert("hello world\n")

    def test_no_delegate_render_methods(self):
        class RendererMixin:
            def render_paragraph(self, element):
                return "ohohohohohoh"

        class Extension:
            renderer_mixins = [RendererMixin]

        markdown = marko.Markdown(renderer=ASTRenderer, extensions=[Extension])
        res = markdown.convert("Hello world")
        paragraph = res["children"][0]
        assert isinstance(paragraph, dict)
        assert paragraph["element"] == "paragraph"

        raw_text = paragraph["children"][0]
        assert raw_text["children"] == "Hello world"
