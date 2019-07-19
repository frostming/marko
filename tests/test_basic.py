#! -*- coding: utf-8 -*-
import unittest
import marko


class TestBasic(unittest.TestCase):

    def test_xml_renderer(self):
        from marko.ast_renderer import XMLRenderer

        text = "[Overview](#overview)"
        markdown = marko.Markdown(renderer=XMLRenderer)
        res = markdown(text)
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', res)
        self.assertIn('dest="#overview"', res)

    def test_ast_renderer(self):
        from marko.ast_renderer import ASTRenderer

        text = "[Overview](#overview)"
        markdown = marko.Markdown(renderer=ASTRenderer)
        res = markdown(text)
        self.assertIsInstance(res, dict)
        self.assertEqual(res['element'], 'document')
        self.assertEqual(res['children'][0]['element'], 'paragraph')


class TestExtension(unittest.TestCase):

    def test_extension_use(self):
        from marko.ext.footnote import FootnoteExtension
        from marko.ext.toc import TocExtension

        markdown = marko.Markdown()
        markdown.use(FootnoteExtension)
        markdown.use(TocExtension)

        self.assertEqual(len(markdown._parser_mixins), 1)
        self.assertEqual(len(markdown._renderer_mixins), 2)
        self.assertTrue(hasattr(markdown._renderer_mixins[0], 'render_footnote_def'))

    def test_extension_setup(self):
        from marko.ext.footnote import FootnoteExtension
        from marko.ext.toc import TocExtension

        markdown = marko.Markdown()
        markdown.use(FootnoteExtension)

        markdown.convert('abc')
        with self.assertRaises(marko.SetupDone):
            markdown.use(TocExtension)

        self.assertTrue(hasattr(markdown.renderer, 'render_footnote_def'))
