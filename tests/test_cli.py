#! -*- coding: utf-8 -*-
import os
import unittest
import delegator

import marko

SYNTAX_FILE = os.path.join(os.path.dirname(__file__), 'samples', 'syntax.md')


class TestCli(unittest.TestCase):

    def test_version(self):
        c = delegator.run('marko --version')
        self.assertTrue(c.ok)
        self.assertEqual(c.out.strip(), marko.__version__)

    def test_default_render(self):
        c = delegator.run('marko < {}'.format(SYNTAX_FILE))
        self.assertTrue(c.ok)
        self.assertIn('<a href="#overview">Overview</a>', c.out)

    def test_xml_renderer(self):
        c = delegator.run(
            'marko --renderer=marko.ast_renderer.XMLRenderer< {}'
            .format(SYNTAX_FILE)
        )
        self.assertTrue(c.ok)
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', c.out)
        self.assertIn('dest="#overview"', c.out)

    def test_ast_renderer(self):
        from marko.ast_renderer import ASTRenderer

        text = "[Overview](#overview)"
        markdown = marko.Markdown(renderer=ASTRenderer)
        res = markdown(text)
        self.assertIsInstance(res, dict)
        self.assertEqual(res['element'], 'document')
        self.assertEqual(res['children'][0]['element'], 'paragraph')

    def test_invalid_option(self):
        c = delegator.run('marko --parser')
        self.assertFalse(c.ok)
        c = delegator.run('marko --parser=marko.ext.abc.GFMParser')
        self.assertFalse(c.ok)
        c = delegator.run('marko --renderer=marko.ext.gfm.FooParser')
        self.assertFalse(c.ok)
