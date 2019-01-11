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
