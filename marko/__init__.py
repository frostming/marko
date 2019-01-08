#! -*- coding: utf-8 -*-
"""
  _    _     _     ___   _  _    ___
 | \  / |   /_\   | _ \ | |/ /  / _ \
 | |\/| |  / _ \  |   / | ' <  | (_) |
 |_|  |_| /_/ \_\ |_|_\ |_|\_\  \___/

 A markdown parser with high extensibility.

 Licensed under MIT.
 Created by Frost Ming<mianghong@gmail.com>
"""
from .html_renderer import HTMLRenderer
from .renderer import Renderer
from .parser import Parser

__version__ = '0.4.3'


class Markdown(object):
    """The main class to convert markdown documents.

    Attributes:
        parser: an instance of :class:`Parser`
        renderer: an instance of :class:`Renderer`

    :param parser: a subclass or instance of :class:`Parser`
    :param renderer: a subclass or instance of :class:`Renderer`
    """
    def __init__(self, parser=Parser, renderer=HTMLRenderer):
        self.parser = parser if isinstance(parser, Parser) else parser()
        self.renderer = renderer if isinstance(renderer, Renderer) else renderer()

    def convert(self, text):
        """Parse and render the given text."""
        return self.render(self.parse(text))

    def __call__(self, text):
        return self.convert(text)

    def parse(self, text):
        """Call ``self.parser.parse(text)``.

        Override this to preprocess text or handle parsed result.
        """
        return self.parser.parse(text)

    def render(self, parsed):
        """Call ``self.renderer.render(text)``.

        Override this to handle parsed result.
        """
        self.renderer.root_node = parsed
        with self.renderer as r:
            return r.render(parsed)
